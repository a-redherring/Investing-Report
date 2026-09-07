# Ingestion

`src/investment_system/ingestion/` holds live market-data adapters. There is
currently **one**: Finnhub quotes. This is the first piece of code in the
repository that makes a real network call — everything else (indicators,
costs, engine, validation, schema, reports, snapshots) stays offline and
deterministic. Nothing here produces a ranking, a score, or a buy/sell
recommendation, and nothing here changes any asset's hard-gate/risk status
(BTCB2's `blake2b_gate` included) — it only produces a validated,
provenance-tagged data point for something else to use later.

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

## CLI

```bash
investment-system fetch-quote AAPL
investment-system fetch-quote AAPL --db /path/to/snapshots.sqlite3   # default: data/snapshots.sqlite3,
                                                                       # or $INVESTMENT_SYSTEM_SNAPSHOT_DB
```

Prints the quote (or `{"error": "...", "message": "..."}`) and exits `1` on
any `IngestionError` — this is the "deterministic callable/CLI boundary" a
scheduler (e.g. a Fedora systemd timer) can invoke without importing
`ingestion.finnhub` directly or knowing anything about Finnhub's response
shape. **Not wired into any systemd unit yet** — that's Fedora-deployment
scope, not this module's.

## What's NOT here yet

- **No historical/weekly-candle ingestion.** `indicators.calculate()` needs a
  time series of weekly closes; `fetch_quote()` returns a single point-in-time
  quote. Feeding the technical-signal pipeline from Finnhub requires a
  candle/history endpoint, which isn't implemented — partly because Finnhub's
  historical-candle access varies by pricing tier and hasn't been confirmed
  for this operator's plan, and building it on a guess would risk silently
  producing wrong indicator values.
- **No BTCB2/Neoxa adapter.** Finnhub doesn't cover Neoxa Exchange; nothing in
  this module fetches or validates BTCB2 prices. See
  [`docs/candidates/BTCB2.md`](../candidates/BTCB2.md) for BTCB2's current
  status against the crypto asset inclusion gate.
- **Not called automatically by anything.** No cron/systemd/CLI-chain invokes
  `fetch-quote` yet; it's a manual/scriptable command today.
- **Only one endpoint, one provider.** `ingestion.errors` is written to be
  provider-agnostic for when a second adapter exists, but there's only one
  today.
