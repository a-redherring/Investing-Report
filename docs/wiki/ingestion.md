# Ingestion

`src/investment_system/ingestion/` holds live market-data adapters. There are
currently **four**: Finnhub quotes, Yahoo Finance weekly candles, and two
Fear & Greed sentiment feeds (Alternative.me for crypto, CNN for equities).
These are the only pieces of code in the repository that make real network
calls — everything else (indicators, costs, engine, validation, schema,
reports, snapshots) stays offline and deterministic. Nothing here produces a
ranking, a score, or a buy/sell recommendation, and nothing here changes any
asset's hard-gate/risk status (BTCB2's `blake2b_gate` included) — it only
produces a validated, provenance-tagged data point for something else to use
later.

## Design contract (every adapter should follow this)

- **Fail closed.** A missing API key, a transport/HTTP failure (rate limits
  included), a malformed or incomplete response, or data older than a
  configured maximum age all raise — never a silent fallback or a best-effort
  guess.
- **Never call the network from a unit test.** The HTTP transport is
  dependency-injected (`transport: Callable[[Request], bytes]`), defaulting to
  a real `urllib`-based implementation. Tests always pass a fake that returns
  fixture bytes or raises directly — see `tests/test_ingestion_finnhub.py`.
- **The API key is a header, never the URL/query string** — so it can't end
  up in a logged URL, proxy log, browser history, or a snapshot's own
  metadata.
- **Snapshot the raw response before validating it.** Evidence of what the
  provider actually sent is preserved even when the response turns out to be
  malformed or stale and the call ultimately raises. See
  `test_malformed_json_is_snapshotted_before_being_rejected` and
  `test_stale_quote_is_snapshotted_before_being_rejected`.

## Finnhub (`ingestion.finnhub`)

```python
from investment_system.ingestion.finnhub import fetch_quote
from investment_system.snapshots import SnapshotStore

with SnapshotStore("data/snapshots.sqlite3") as store:
    quote = fetch_quote("AAPL", snapshot_store=store)  # reads FINNHUB_API_KEY
    # quote.current, .high, .low, .open, .previous_close, .quoted_at,
    # .retrieved_at, .snapshot_id
```

Config lives in `config/data-sources.yaml` (`ingestion.data_sources.FinnhubConfig`):
provider name, base URL, the *name* of the API-key environment variable (not
the key itself), a request timeout, and a max quote age (default 3600s) after
which a quote is rejected as stale.

`fetch_quote()` calls Finnhub's `/quote` endpoint and validates the response:

- All of `c` (current), `h`/`l`/`o` (high/low/open), `pc` (previous close),
  and `t` (unix timestamp) must be present and numeric.
- Finnhub returns **HTTP 200 with every field zeroed** for a symbol it
  doesn't recognize, rather than a 4xx — treating that as a real zero price
  would be wrong, so it's explicitly detected and rejected
  (`IngestionResponseError: ... unrecognized symbol ...`).
- `t` is converted to a UTC timestamp and compared against `max_quote_age_seconds`;
  too old raises `IngestionStaleDataError`.

### Errors (`ingestion.errors`)

`IngestionError` is the base class; every adapter should raise from this
hierarchy rather than a bare `Exception` or provider-specific type, so a
caller can catch `IngestionError` generically:

| Exception | Raised when |
|---|---|
| `IngestionConfigError` | Missing/invalid config, or `FINNHUB_API_KEY` unset |
| `IngestionRequestError` | Network error or non-2xx HTTP status |
| `IngestionRateLimitError` | HTTP 429 specifically (subclass of the above) |
| `IngestionResponseError` | Malformed JSON, missing fields, or Finnhub's all-zero "unrecognized symbol" response |
| `IngestionStaleDataError` | The quote's own timestamp is older than `max_quote_age_seconds` |

## Historical weekly candles (`ingestion.yahoo`)

Feeding `indicators.calculate()` needs a real time series of weekly closes,
which a single quote can't provide. Provider research (2026-09-07, before
building anything) ruled out every free candidate but one:

| Provider | Verdict |
|---|---|
| Finnhub free tier | Empirically confirmed blocked — `403` on every candle call (stock and crypto), tested against a real key |
| Alpha Vantage free tier | No ASX coverage at all — empirically confirmed, zero Australia-region matches in `SYMBOL_SEARCH` |
| Twelve Data free tier | Explicitly US-equities-only by their own pricing page |
| Stooq | Free CSV in the right shape, but now gated by a client-side JS proof-of-work challenge — not automatable headlessly |
| CoinGecko | Solid for BTC daily prices, but the public/free-Demo tier hard-caps historical range at 365 trailing days (`error_code 10012`) — not enough for a 200-week MA. Considered and **removed**; see [Changelog](changelog.md) |
| **Yahoo Finance's chart endpoint** | **Used.** Free, unauthenticated, real multi-year weekly OHLC for every asset tested, ASX-listed ETFs and BTC-USD alike |

```python
from investment_system.ingestion.yahoo import fetch_weekly_history
from investment_system.snapshots import SnapshotStore

with SnapshotStore("data/snapshots.sqlite3") as store:
    bars = fetch_weekly_history("IVV.AX", snapshot_store=store, range_="10y")
    # bars: list[WeeklyBar(date="YYYY-MM-DD", close=...)], oldest first
```

Config lives in `config/data-sources.yaml` (`ingestion.data_sources.YahooConfig`):
provider name, base URL, the User-Agent header (Yahoo's endpoint requires
one), and a request timeout. No API key exists or is needed.

**Two real problems were found and fixed empirically, not guessed at, before
this shipped** — see [Changelog](changelog.md#2026-09-07) for the full story:

1. **`range="max"` silently coarsens to monthly bars**, despite
   `interval=1wk` being requested, with no error or signal in the response.
   `fetch_weekly_history()` therefore never uses Yahoo's own `"max"` — it
   defaults to an explicit `"20y"`, confirmed to return genuine, gap-free
   7-day-delta weekly bars for every ticker tested.
2. **Yahoo's `"IVV.AX"` history is corrupted from 2010 to 2017** — real
   values repeatedly flip-flop ~15x against bogus ones, with no stock split
   recorded to explain it (confirmed against `events=splits` and by checking
   both raw `close` and `adjclose`). Every other tested ticker (VAS, VGS,
   NDQ, IZZ, VAE, BTC-USD) has no such anomaly. `_parse_weekly_history()`
   therefore rejects **any** single-week close-to-close move beyond a 5x/0.2x
   sanity bound (comfortably wider than real extreme volatility — BTC's
   genuine ~-33% single-week COVID crash sits well inside it) — a permanent
   safeguard against this class of corrupted data recurring for any ticker,
   not just a one-time workaround for IVV specifically.

## Sentiment (`ingestion.alternative_me`, `ingestion.cnn_fear_greed`)

The report schema's `sentiment.equity_fear_greed` and `sentiment.crypto_fear_greed`
fields need two source-agnostic Fear & Greed observations. Both adapters
return the same shared `ingestion.sentiment.SentimentObservation` (`value`,
`category`, `provider`, `effective_at`, `retrieved_at`, `snapshot_id`) —
mirrors the schema's `sentimentObservation` shape closely enough to embed
directly with `status: "observed"` added at the point of use.

```python
from investment_system.ingestion.alternative_me import fetch_crypto_fear_greed
from investment_system.ingestion.cnn_fear_greed import fetch_equity_fear_greed
from investment_system.snapshots import SnapshotStore

with SnapshotStore("data/snapshots.sqlite3") as store:
    crypto = fetch_crypto_fear_greed(snapshot_store=store)   # no key needed
    equity = fetch_equity_fear_greed(snapshot_store=store)   # no key needed
```

**Crypto: Alternative.me's `/fng/` endpoint** — an official, documented, free
API, no key required. Category strings are Title Case as the provider sends
them ("Greed", "Extreme Fear", etc.), passed through unchanged rather than
normalized.

**Equity: CNN's unofficial chart-data endpoint** — the same provenance and
risk profile as `ingestion.yahoo`: no ToS support, no SLA, and it actively
blocks plain requests. Confirmed 2026-09-07: a request with no `Referer`
header returns the literal plain-text body `"I'm a teapot. You're a bot."`
(not JSON, not an HTTP error status — `_parse()` must and does treat this as
a malformed-response case, not crash on it); adding a browser-like
`User-Agent` plus a `Referer` matching the real page (`cnn.com/markets/fear-and-greed`)
is enough to pass. No official free alternative was found for CNN's Fear &
Greed Index specifically — the schema's `equity_fear_greed` field name was
clearly written with this exact index in mind, so it's used with the
unofficial-source caveat stated plainly rather than substituted with a
worse, differently-defined index.

Both fail closed on a reading older than a configured `max_age_seconds`
(`config/data-sources.yaml`): 2 days for crypto (updates daily, every day —
24/7 markets), 4 days for equities (accounts for a normal Friday-to-Monday
weekend gap when equity markets are closed).

## CLI

```bash
investment-system fetch-quote AAPL
investment-system fetch-quote AAPL --db /path/to/snapshots.sqlite3   # default: data/snapshots.sqlite3,
                                                                       # or $INVESTMENT_SYSTEM_SNAPSHOT_DB

investment-system fetch-history IVV                # writes data/history/IVV.csv (asset,date,close)
investment-system fetch-history BTC --range 15y     # override the per-asset default Yahoo range

investment-system fetch-sentiment crypto            # Alternative.me, no key needed
investment-system fetch-sentiment equity            # CNN, no key needed
```

`fetch-quote`/`fetch-sentiment` print the fetched value (or
`{"error": "...", "message": "..."}`) and exit `1` on any `IngestionError` —
this is the "deterministic callable/CLI boundary" a scheduler (e.g. a Fedora
systemd timer) can invoke without importing any adapter module directly or
knowing anything about a provider's response shape. **None of the four
adapters are wired into any systemd unit yet** — that's Fedora-deployment
scope, not this module's.

`fetch-history <ASSET>` only accepts an asset symbol with a configured
provider mapping — currently IVV, NDQ, VAS, VGS, IZZ, VAE, GOLD (all via
Yahoo, `<SYMBOL>.AX`) and BTC (Yahoo, `BTC-USD`). CASH has no price series
to fetch. The output CSV is written in the exact `asset,date,close` shape
`engine.load_prices()` already expects, so it can be fed straight into
`investment-system signals` with no other change.

### Gold vehicle selection (`GOLD.AX`)

Gold's vehicle was an explicit open design question (which instrument,
hedged or unhedged, in which currency) independent of any data provider's
API — resolved 2026-09-07 to **ASX:GOLD** (Global X Physical Gold,
unhedged, AUD), after comparing it against the other ASX-listed gold ETFs
on both data quality and economic exposure:

| Candidate | Yahoo data quality | History | Decision |
|---|---|---|---|
| **GOLD.AX** (unhedged) | One isolated bad tick (2010-12-26→2011-01-02); clean otherwise | 976 bars since 2007 | **Chosen** — largest/most liquid ASX gold ETF, matches the symbol already in `config/universe.yaml` |
| QAU.AX (hedged into AUD) | Completely clean | 802 bars since 2011 | Considered — pure gold-price exposure, no AUD-weakness diversification benefit, higher fee (0.59% vs 0.40%) |
| PMGOLD.AX (unhedged) | **Unreliable** — `fiftyTwoWeekHigh` ($78.99) vs `regularMarketPrice` ($17.94) is a >4x disparity with no split recorded, plus intermittent monthly-spaced gaps as recently as 2020 | — | Ruled out on data reliability |
| NUGG.AX (unhedged) | Clean | Only 197 bars since Dec 2022 (~3.8 years) | Ruled out — too little history for a 200-week MA |

Like `IVV.AX`, `GOLD.AX`'s isolated bad tick sits right at the same
2010-2011 boundary IVV's sustained corruption occupies — pinned to
`range="15y"` (784 clean bars, confirmed zero anomalies) in `cli.py`'s
per-asset provider table, well past that point.

## What's NOT here yet

- **No BTCB2 adapter.** No configured provider covers BTCB2's trading venue;
  nothing in this module fetches or validates BTCB2 prices. See
  [`docs/candidates/BTCB2.md`](../candidates/BTCB2.md) for BTCB2's current
  status against the crypto asset inclusion gate.
- **Not called automatically by anything.** No cron/systemd/CLI-chain invokes
  `fetch-quote`, `fetch-history`, or `fetch-sentiment` yet; all are
  manual/scriptable commands today, and none feed `reports/`, rankings, or
  gates.
- **Yahoo's and CNN's endpoints are unofficial and undocumented** — no ToS
  support, no SLA, no guarantee either won't change or start rate-limiting
  without notice. Used because each is empirically the only free source
  found for what it provides (real multi-year ASX weekly history; the
  specific index the schema's `equity_fear_greed` field was named after);
  the fail-closed design here means a future breakage surfaces as a loud
  `IngestionError`, not silently wrong indicators or sentiment.
