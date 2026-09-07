# ============================================================
# FULL PROGRAM DESCRIPTION — Monday Investment Decision System
# ============================================================
#
# Purpose of this document: a single, self-contained specification of the
# entire program — policy, data model, architecture, and current build
# status — sufficient to rebuild it from scratch without needing to read
# the wider design doc, wiki, or conversation history. Where this
# document and the code disagree in the future, the code is right and
# this document is stale; treat that as a bug.
#
# Generated: 2026-09-07, from the actual current repository state
# (`config/*.yaml`, `schemas/frozen-report.schema.json`,
# `src/investment_system/`, `tests/`, `docs/`) — not from memory.

## 1. What this program is

A personal, single-operator research tool that produces one disciplined,
auditable investment decision each Monday from a deliberately small,
closed universe of assets. It is **not** an automated trading bot, not
financial advice, and does not place trades. It answers five questions
each week:

1. What are the three best uses of new money this week?
2. Does any risk asset clear the hurdle set by cash yielding an assumed 5%?
3. If an asset wins, is the evidence strong enough for A$999, A$2,000, or A$4,000?
4. Should any existing position be held, reduced, or sold?
5. Was the decision process consistent, reproducible, and honest about uncertainty?

The system separates four distinct layers, never collapsed into one another:

- **Deterministic calculations** — pure functions over historical price
  data (moving averages, RSI, MACD, brokerage fees). No judgment, no
  network calls, same input always produces the same output.
- **Qualitative analysis** — fundamental/regime/sentiment judgment,
  currently a human/interactive-AI task, not automated.
- **Model classifications** — the labels the deterministic layer emits
  (`Extended`, `Strong Uptrend`, etc.).
- **Final decisions** — what actually gets recorded in a frozen report.

### Non-negotiable constraints (apply to every layer)

- No API key, token, credential, account identifier, or other secret ever
  belongs in reports, logs, fixtures, commits, screenshots, or issues.
- Fail closed on missing/stale/malformed data — never guess, never
  silently substitute a default for something that should be "unknown."
- The investable universe is **closed by default**. Adding any asset
  requires an explicit model-version change, data specification, fee
  model, asset-specific overlay, and benchmark treatment — never a silent
  config edit.
- Live decisions happen **only on Monday** (`Australia/Sydney`). Any other
  day's output must be labelled `Practice Report P-###` or `Preview` and
  state it is non-live.
- **Preserve the record.** Never rewrite an old live report using
  information learned later. Corrections are appended as errata, not
  silent edits.
- No automated trade execution exists or is authorised anywhere in this
  design.

## 2. The tracked universe (current, Model v1.0)

| Asset | Role | Core holding? |
|---|---|---:|
| IVV | US large-cap equities | Yes |
| NDQ | Nasdaq-100 growth tilt | No |
| VAS | Australian equities | Yes |
| VGS | Developed global equities | Yes |
| IZZ | China large-cap exposure | No |
| VAE | Asian equities ex-Japan | Yes |
| GOLD | Diversifier / real asset | No |
| BTC | High-volatility cyclical asset | No |
| CASH | Reserve and benchmark, assumed 5% p.a. | N/A |

**Core holdings** (IVV, VAS, VGS, VAE) receive a **Waiting Risk**
assessment (Low/Medium/High) — a separate judgment about the opportunity
cost of remaining in cash rather than accumulating. It lets a moderately
expensive core ETF still qualify for the A$999 accumulation tier; it never
by itself justifies A$2,000 or A$4,000. BTC, GOLD, NDQ, and IZZ do **not**
get this privilege — they must clear their own higher, asset-specific
hurdle every time.

There is **no blanket ban on cryptocurrencies other than BTC** — but
adding one requires clearing the crypto asset inclusion gate (§7) on top
of the standard closed-universe process. In practice there is currently
exactly one tracked candidate, **BTCB2**, which is *not* in the universe
(see §7 and §20).

## 3. Fee-aware sizing

| Decision | Meaning |
|---:|---|
| **A$0** | Cash wins — no candidate offers sufficient expected reward for its risk/costs |
| **A$999** | Accumulation capital — maintain participation in a core compounder, or a modest starter position |
| **A$2,000** | Opportunity capital — genuinely attractive setup with adequate confirmation |
| **A$4,000** | Dislocation capital — rare, exceptional setup: major mispricing or capitulation, thesis intact |

Working ASX brokerage assumption (CMC Invest Australia, **must be
re-verified before any live decision that relies on it**): a qualifying
first buy under A$1,000 per security per day gets A$0 brokerage; otherwise
`max(A$11, 0.10% of order value)`. Formula (`costs.asx_brokerage`):

```
if qualifying_buy and amount_aud <= 999: fee = 0.0
else: fee = max(minimum_aud, amount_aud * rate_pct / 100)
```

With the committed defaults (`minimum_aud=11.0`, `rate_pct=0.10`,
`qualifying_buy_limit_aud=999.0`): A$999 buy → A$0 (0.000% drag); A$2,000
buy → A$11 (0.550%); A$4,000 buy → A$11 (0.275%). BTC is sized in
approximate A$1,000/2,000/4,000 equivalents after its own venue costs — it
does **not** receive the ASX A$999 brokerage-free treatment. Every
recommendation must also weigh bid/ask spread, FX conversion, ETF
management fees/tracking difference, crypto exchange/network/custody
costs, tax, liquidity/execution quality, and the cost of *selling*, not
just buying — "brokerage free" never means economically free.

## 4. The three-layer per-asset model

Every risk asset gets three **separately labelled** layers — never
collapsed into one score:

### 4a. Fundamental / macro valuation
`Very Cheap` / `Cheap` / `Fair` / `Expensive` / `Very Expensive` /
`Insufficient Data`. Inputs vary by asset (earnings yield, multiples,
dividend yield, growth, real yields, credit conditions, inflation,
currency, adoption, valuation vs. history/peers). **Never** inferred
solely from distance to a moving average — price can be technically
extended while fundamentally cheap, or vice versa.

### 4b. Technical stretch and trend

Computed deterministically from weekly closing prices only (see §10 for
exact formulas): 20W/50W/200W simple moving averages, weekly RSI (Wilder's
smoothing, period 14), MACD (12/26/9), distance-from-MA percentages,
drawdown from all-time high, a stretch label, an MA-slope label, and a
trend label (`Insufficient Data` / `Strong Uptrend` / `Uptrend` / `Mixed` /
`Downtrend` / `Strong Downtrend`).

### 4c. Regime / sentiment
Equity and crypto Fear & Greed-style observations, each either `observed`
(with value, category, provider, effective time, retrieval time) or
`unavailable` (with an explicit reason) — never silently blank.

### 4d. Waiting Risk (core holdings only)
See §2.

## 5. Bitcoin-specific rules

Every report carries **independent** BTC BUY and BTC SELL assessments —
never substituted for one another, never merged into one label.

- **BTC BUY** allowed states: `BUY`, `WATCH`, `NO_BUY`, `INSUFFICIENT_DATA`
  (dollar sizing tier recorded separately). Must cover cycle phase,
  drawdown from ATH, 20W/50W/200W position, weekly RSI/MACD, crypto
  sentiment, liquidity/regime, thesis risks, venue costs.
- **BTC SELL** allowed states: `HOLD`, `CONSIDER_PARTIAL_SELL`,
  `PARTIAL_SELL`, `EXIT`, `INSUFFICIENT_DATA`. Uses a fixed reference basis
  of **US$60,000**: `gain_from_reference_pct = (btc_price_usd / 60000 - 1) * 100`
  — context for the decision, never itself a reason to avoid a rational
  sale. A partial sell needs confluence: failed weekly resistance, loss of
  the 50W after a bear rally, deteriorating momentum, Greed, weakening
  liquidity, or thesis impairment.

### Bitcoin BLAKE2b monitoring (unconditional, separate from §7)

Every report separately monitors the proposed Bitcoin proof-of-work change
from SHA256d to BLAKE2b — not ordinary BTC price analysis, and this runs
regardless of whether any BLAKE2b-related asset is in the universe. Each
report records either a material, sourced development, or the fixed line
`No sufficiently credible BLAKE2b development changes the portfolio
decision this week.`

## 6. Crypto asset inclusion gate

A cryptocurrency other than BTC becomes eligible for a **new
model-version change proposing its addition** only when all six of the
following are independently verified and recorded, with sources, across
**≥4 consecutive Monday reports** (live or practice) with no regression:

1. **Operational maturity** — mainnet live ≥3 months, no unresolved
   consensus-halting incident during that period.
2. **Liquidity** — ≥US$250,000 trailing-30-day average daily volume,
   aggregated across ≥2 independent, non-affiliated exchanges. A single
   venue never satisfies this alone.
3. **Price discovery** — ≥2 independent venues quote the reference pair,
   <5% price divergence between them at check time.
4. **Custody** — a self-custody path via open-source wallet software, or a
   recognized third-party custodian/hardware wallet. Exchange-only
   custody does not satisfy this.
5. **Independent verifiability** — a public block explorer and node
   software independent of any single exchange.
6. **Defined thesis and risk model** — a written, dated investment thesis
   and explicit invalidation conditions exist, addressing plausibility and
   risk modelling against the vulnerabilities the candidate responds to.
   (This requirement is about the thesis *existing*, not about proving the
   underlying belief correct — ongoing truth is tracked via the
   invalidation conditions in every future report, not re-litigated from
   scratch each time.)

These thresholds are an explicit, adjustable working default — the
operator may tighten, loosen, or even remove a criterion via a
model-version change (this has already happened once: an original seventh
criterion, an independent security/code audit, was proposed and then
removed as impractical). Clearing the gate still does **not** grant an
automatic BUY tier — the asset then enters the universe on equal footing
with everything else, subject to its own venue/liquidity/security overlay
and the full three-layer model.

**Tracking convention:** since report generation doesn't exist yet (§20),
per-candidate gate status lives in `docs/candidates/<SYMBOL>.md` — one
section per criterion (requirement / status / evidence-source /
last-reviewed), plus the written thesis and invalidation conditions under
criterion 6, plus an overall status table. See `docs/candidates/BTCB2.md`
for the only current example.

## 7. Ranking and decision rules

Every live report ranks the entire universe and highlights **#1 —
preferred use of new money**, but ordinarily selects **at most one**
new-money action across the whole universe. If no asset clears the cash
hurdle, the correct decision is **A$0 invested** — this is a valid,
expected outcome, not a failure state.

## 8. Data model — the frozen-report contract

`schemas/frozen-report.schema.json` (JSON Schema draft 2020-12) is the
**structural** contract; `validation.validate_report()` adds the
cross-field **business** rules the schema can't express. Both together are
the canonical contract — this document is explanatory, not authoritative;
if it drifts from the schema, the schema wins.

### Top-level required fields
`schema_version` (const `"1.0"`), `report_id`, `report_kind`
(`practice`|`live`), `model_version`, `decision_date` (date),
`timezone` (const `"Australia/Sydney"`), `data_cutoff` (date-time),
`generated_at` (date-time), `assumptions`, `rankings`, `bitcoin`,
`sentiment`, `quality_control`. Optional: `code_commit`,
`input_snapshot_id`.

### `report_id` / `report_kind` coupling (business rule, not schema)
Practice reports require `P-###`; live reports require `###` — the schema
alone accepts either pattern for either kind, so this relationship is
enforced by `validate_report()`, not the schema.

### `rankings[]` (min 1 item)
Each entry: `rank` (int ≥1), `asset`, `new_money_action` (`A$0`|`A$999`|
`A$2000`|`A$4000`|`BTC_EQUIVALENT`), optional `existing_position_action`
(`HOLD`|`CONSIDER_PARTIAL_SELL`|`PARTIAL_SELL`|`EXIT`), `confidence`
(`high`|`medium`|`low`|`insufficient`), `hard_gates_passed` (bool),
`rationale`. Business rules: ranks must be unique integers, contiguous
from 1; a `live` report's `decision_date` must fall on a Monday
(`weekday() == 0`); optionally, every configured universe asset must
appear (default on — `check_universe_coverage`).

### `bitcoin`
`status` (`available`|`unavailable`), optional `reference_basis`
(`currency`/`price`/`as_of`), required `buy_assessment` and
`sell_assessment` (see §5 for enums; each needs `decision`, `confidence`,
`rationale`), required `blake2b_gate` (`status`: `pass`|`fail`|
`unavailable`, optional `checked_at`, `reason`). Business rule: if a BTC
assessment is `INSUFFICIENT_DATA` or the gate is `unavailable`, a
rationale/reason is required — never silently blank. (There is
deliberately **no** `operator_thesis` sub-field — it was built, then
removed entirely on 2026-09-07 as irrelevant; don't re-add it.)

### `sentiment`
`equity_fear_greed` and `crypto_fear_greed`, each: `status`
(`observed`|`unavailable`), `value` (0-100 or null), `category`,
`provider`, `effective_at`, `retrieved_at`, optional `reason`. Business
rule: `unavailable` needs a `reason`; `observed` needs `value`,
`provider`, `effective_at`, and `retrieved_at` all present.

### `quality_control`
`validation_status` (`pass`|`fail`|`practice_only`), `warnings` (array of
strings).

## 9. Repository architecture

```
config/
  model-v1.0.yaml       brokerage + cash-yield parameters for the current model version
  universe.yaml          tracked asset list (§2)
  data-sources.yaml       Finnhub base URL, API-key env var name, timeouts
src/investment_system/
  config.py               loads/type-checks the YAML config files, portable path resolution
  indicators.py            SMA/EMA/RSI/MACD, stretch/trend classification, MA slope
  costs.py                 ASX brokerage fee calculation (pure function, no I/O)
  validation.py            fail-closed CSV/report input validation, structured issues
  schema.py                loads schemas/frozen-report.schema.json, runs JSON Schema validation
  snapshots.py             append-only SQLite store for raw input snapshots (SnapshotStore)
  reports.py               canonical JSON report validation, hashing, write-once freeze
  ingestion/               live market-data adapters (currently: Finnhub quotes only)
    errors.py                shared IngestionError hierarchy
    data_sources.py           loads config/data-sources.yaml
    finnhub.py                 fetch_quote(): fetch, snapshot, validate
  engine.py                wires config.py + indicators.py + costs.py + schema.py +
                            validation.py + snapshots.py together; the module other
                            code (CLI) actually calls
  cli.py                   `investment-system` command-line entry point
schemas/                 frozen-report JSON Schema (§8)
reports/practice/         illustrative schema-shaped practice artifact only (P-001.example.json)
docs/candidates/          per-candidate crypto-asset-inclusion-gate tracking (§6)
tests/                   one test module per src module, plus fixtures
data/                    snapshots.sqlite3 lives here by default (gitignored)
deploy/systemd/          Fedora service/timer templates (not enabled — §17)
scripts/                 Fedora offline healthcheck
```

### Data flow

```
CSV (asset,date,close)
  -> engine.load_prices()        groups by asset, sorts by date, rejects duplicate
                                   (asset,date) rows and invalid prices
  -> indicators.calculate()      one snapshot per asset (§10)
  -> engine.calculate_signals()  dict of asset -> snapshot fields (CLI/JSON output)

config/*.yaml
  -> config.load_model_config()/load_universe()
  -> engine.cost_table()         fee schedule for 999/2000/4000 tiers
  -> engine.config_snapshot()    what `investment-system config` prints

Report JSON
  -> schema.schema_errors()          structural check (§8)
  -> validation.validate_report()    cross-field business rules
  -> engine.validate_report()        both together, + universe coverage + optional
                                       snapshot-id verification against the store

Snapshot store (data/snapshots.sqlite3)
  -> snapshots.SnapshotStore.save()  content-identified, append-only (§13)

config/data-sources.yaml
  -> ingestion.finnhub.fetch_quote(symbol, snapshot_store=...)  (§14)
```

## 10. Deterministic indicators (exact formulas)

All inputs are weekly closing prices, oldest first, no external data.

- **`sma(values, period)`** — simple moving average of the last `period`
  values; `None` if fewer are available (never approximated).
- **`ema` / MACD** — EMA seed = simple average of the first `period`
  values, standard recursion after that. `macd_line = EMA(12) - EMA(26)`
  (needs ≥26 values); `macd_signal = EMA(9)` of the MACD-line history
  (needs ≥34 values total — legitimately `None`, not a bug, for 26-33);
  `macd_histogram = line - signal`.
- **`rsi(values, period=14)`** — **Wilder's smoothing** (matches
  brokers/charting platforms), not Cutler's plain trailing average:
  ```
  avg_gain (seed) = mean(first period gains); avg_loss (seed) = mean(first period losses)
  avg_gain = (avg_gain * (period - 1) + gain) / period   # repeated for every later change
  avg_loss = (avg_loss * (period - 1) + loss) / period
  RSI = 100 - 100 / (1 + avg_gain / avg_loss)
  ```
  Depends on the *entire* price history, not just the trailing window, and
  is order-dependent. Needs `period + 1` values. All-losses → `0.0`;
  no-change series → `50.0`.
- **Distances**: `distance_from_ma_pct = (close / ma - 1) * 100` per MA;
  `drawdown_from_ath_pct = (close / max(values) - 1) * 100` (≤0).
- **Stretch label** (from `distance_20w_pct` = `d20`): `Insufficient Data`
  if `ma_20w` unavailable; `d20≥20` → `Extremely Extended`; `d20≥8` →
  `Extended`; `d20≤-20` → `Deeply Oversold`; `d20≤-8` → `Oversold`; else
  `Normal`. (Unvalidated first-pass thresholds, expected to move once
  calibrated.)
- **MA slope** (`slope_50w`/`slope_200w`): compares the current
  `period`-week SMA to the same SMA 4 weeks earlier (`SLOPE_LOOKBACK_WEEKS
  = 4`). `Rising`/`Falling`/`Flat`, or `None` if either SMA is unavailable
  — needs `period + 4` values, 4 more than the MA itself.
- **Trend label** (`_classify_trend`, uses close vs. `ma_50w`, `ma_50w` vs.
  `ma_200w` golden/death cross, and `slope_50w`; `slope_200w` is reported
  but doesn't currently gate the label):

  | close vs. ma_50w | ma_50w vs. ma_200w | slope_50w | Label |
  |---|---|---|---|
  | — | — | — | `Insufficient Data` if ma_50w is None |
  | above | below (death cross) | any | `Mixed` |
  | above | above/unknown | Rising | `Strong Uptrend` |
  | above | above/unknown | not Rising | `Uptrend` |
  | below/equal | above (golden cross) | any | `Mixed` |
  | below/equal | below/unknown | Falling | `Strong Downtrend` |
  | below/equal | below/unknown | not Falling | `Downtrend` |

  `Mixed` covers exactly the two cases where short-term price and
  long-term MA structure disagree.

## 11. Config layer

`config.resolve_repo_root()`/`resolve_config_dir()` resolve fresh on every
call (no import-time caching), checked in order: the
`INVESTMENT_SYSTEM_CONFIG_DIR` env var (config only, explicit override) →
a `config/`/`schemas/` directory under cwd or a parent (the documented
"run from within a clone" workflow) → the path relative to the installed
package (works for an editable/source install regardless of cwd). Fails
closed with an actionable `FileNotFoundError` listing every directory
checked if none work.

Current committed `config/model-v1.0.yaml`:
```yaml
model_version: "1.0"
cash_yield_pct: 5.0
brokerage:
  minimum_aud: 11.0
  rate_pct: 0.10
  qualifying_buy_limit_aud: 999.0
```

Current committed `config/universe.yaml`: the 9 assets in §2, each as
`{symbol, currency, core}`.

## 12. Snapshot store (provenance)

`snapshots.SnapshotStore` — append-only, SQLite-backed
(`data/snapshots.sqlite3` by default), content-identified:
`id = sha256(source + retrieved_at + content)`. Identical
`(source, retrieved_at, content)` twice is a no-op (same row); any change
to `content` is always a **new** row, never an overwrite — enforced by
SQLite triggers rejecting direct `UPDATE`/`DELETE`, not just by
application logic. Every row also records `stored_at` (when this process
wrote it) and `content_sha256` (integrity check without re-deriving the
id). No pruning/retention policy — genuinely append-only forever, judged
fine at today's personal-research scale.

API: `store.save(source, content, retrieved_at=None, metadata=None)`,
`store.get(id)`, `store.list(source=None)`, `snap.summary()` (every field
except `content`, for cheap listing).

## 13. Ingestion adapters

One adapter exists: **Finnhub single quotes**
(`ingestion.finnhub.fetch_quote`) — the only code in the repository that
makes a real network call; everything else stays offline and
deterministic. Design contract every future adapter should follow:

- **Fail closed.** Missing API key → `IngestionConfigError`, transport
  never called. Transport/HTTP failure (rate limits included) →
  `IngestionRequestError`/`IngestionRateLimitError`. Malformed/incomplete/
  Finnhub's documented all-zero "unrecognized symbol" response →
  `IngestionResponseError` — **but the raw response is snapshotted
  first**, so rejected evidence remains auditable. A quote older than
  `max_quote_age_seconds` (config default 3600s) → `IngestionStaleDataError`,
  also snapshotted first.
- API key sent as an `X-Finnhub-Token` **header**, never in the URL/query
  string.
- No test ever touches a real socket — the HTTP transport is
  dependency-injected; every test supplies a fake.
- Deterministic CLI boundary: `investment-system fetch-quote <symbol>`
  exits 1 with a structured JSON error on any `IngestionError` — a
  scheduler can invoke it without importing anything from `ingestion`.
- **Does not** feed the indicator pipeline (a single quote can't produce
  20W/50W/200W indicators — that needs historical/weekly-candle ingestion,
  which doesn't exist yet, §20) and **does not** touch rankings, gates, or
  recommendations.

## 14. Report validation and freezing

`engine.validate_report(report, check_universe_coverage=True,
snapshot_db=None)` runs the JSON Schema (§8) and the business rules (§10
of the schema section above) together, defaulting expected assets to the
real `config/universe.yaml`; optionally verifies `input_snapshot_id`
against a snapshot store if `snapshot_db` is given.

`reports.freeze_report(report, output_dir, check_universe_coverage=True,
confirmed=False)` — **requires explicit `confirmed=True`** (mutation
confirmation — the CLI's `--confirm-freeze` flag). Validates first, then
writes **canonical JSON** (`json.dumps(..., sort_keys=True,
separators=(",",":"))`, trailing newline) plus a `.sha256` sidecar.
Idempotent for identical content (re-freezing the same report ID with
byte-identical content is a no-op, `status: already_frozen`); raises
`FileExistsError` for the same report ID with *different* content — an
existing frozen report is **never** overwritten, ever.

## 15. CLI reference

```
investment-system signals <csv>                                    per-asset indicator snapshot as JSON
investment-system costs                                            fee schedule for A$999/2,000/4,000
investment-system config                                           parsed model config + universe
investment-system validate-report <path> [--no-universe-check] [--snapshot-db PATH]
investment-system freeze-report <path> [--output-dir DIR] [--no-universe-check] --confirm-freeze
investment-system snapshot-save <source> <path> [--retrieved-at ISO8601] [--metadata JSON] [--db PATH]
investment-system snapshot-get <snapshot_id> [--db PATH]
investment-system snapshot-list [--source NAME] [--db PATH]
investment-system fetch-quote <symbol> [--db PATH]                 needs FINNHUB_API_KEY; only network-calling command
```

## 16. Testing approach

One test module per `src/investment_system/` module. Principles actually
enforced (not aspirational):

- Every changed formula, validation rule, or schema requirement gets a
  test — including a fully hand-traced golden fixture for RSI
  (`test_rsi_matches_wilders_smoothing_formula`, period=5, worked
  independently of the implementation).
- No test ever touches the network — the Finnhub HTTP transport is
  dependency-injected; every ingestion test supplies a fake transport.
- Config/schema portability tests actually build a wheel, install it in a
  throwaway venv, and run from an unrelated cwd (not just reasoned about).
- Regression tests lock in removed behavior too, not just added behavior
  (e.g. `test_blake2b_gate_rejects_operator_thesis_as_an_unknown_field`
  ensures a deliberately removed field can't silently drift back in).

Currently 65 tests, all offline, `python -m pytest -q`.

## 17. Deployment model

**Fedora only** (desktop for development/testing, home server for
production) — Windows/macOS deployment explicitly out of scope. Secrets
live in `/etc/investing-advice/secrets.env` (or equivalent), never in the
repository; `.env.example` documents variable *names* only
(`FINNHUB_API_KEY`, `INVESTMENT_SYSTEM_CONFIG_DIR`,
`INVESTMENT_SYSTEM_SNAPSHOT_DB`). `deploy/systemd/*.example` provides a
service (runs as a dedicated unprivileged `investing` user,
`ProtectSystem=strict`, `ProtectHome=true`, `NoNewPrivileges=true`) and a
timer (`Mon *-*-* 08:00:00 Australia/Sydney`) — **both explicitly
templates, not enabled**, since the `monday-run` command they reference
doesn't exist yet (§20).

## 18. Planned interactive/review architecture (design only, not built)

The long-range design (not yet implemented) describes an operator running
an interactive AI session (ChatGPT desktop or a Codex-style CLI) with an
MCP server exposing read-only tools over the versioned methodology,
universe, schema, latest validated snapshot, and frozen-report archive —
explicitly **never** exposing `.env`, credentials, account identifiers, or
unrestricted filesystem contents, and **never** providing
`place_trade`/`submit_order`/`transfer_funds`/brokerage-login tools. A live
report can be frozen only on an eligible Monday; the server calculates
indicators/costs/hashes/dates itself rather than trusting the model's
arithmetic; it never permits overwriting an existing frozen report.

## 19. What's built vs. not built (as of 2026-09-07)

**Built and tested:** weekly indicator calculations (§10), ASX brokerage
costs, CSV/report validation, JSON Schema validation, append-only
snapshot storage, explicit-confirmation write-once report freezing, the
Finnhub single-quote adapter, the crypto asset inclusion gate concept and
BTCB2's tracking against it (§6 — currently: custody and independent
verifiability pass on operator-verified evidence, the thesis/invalidation
conditions pass, operational maturity fails outright at ~1 week old,
liquidity and price discovery remain unsourced).

**Not built:** historical/weekly-candle ingestion (a single Finnhub quote
cannot feed the indicator pipeline, which needs a real time series);
sentiment providers; any scoring/ranking/draft-report-generation engine;
the `monday-run` orchestration command; the MCP server (§18); systemd
scheduling actually enabled; benchmark simulation and 4/13/26/52-week
postmortems. **No report has ever been generated by this system** —
`reports/practice/P-001.example.json` is a hand-written illustrative
fixture proving the schema/validator work, not an output of any pipeline.

## 20. Roadmap / build order

1. Historical-candle ingestion + a canonical weekly-price contract
   (verify the chosen provider's actual tier/access before relying on it;
   never infer a weekly series from a single quote).
2. BTCB2/Neoxa adapter + dedicated venue/liquidity/security/custody
   overlay — **gated, not scheduled**: do not build until BTCB2
   independently clears §6's gate and an operator authorizes a new
   model-version change.
3. Decide and document equity/crypto sentiment providers, freshness
   rules, and unavailable-state behavior.
4. Build deterministic feature assembly, scoring, ranking, and
   draft-report generation against the existing schema and practice
   fixture.
5. Add `monday-run`: snapshots inputs, validates freshness and universe
   coverage, writes a draft, never freezes without explicit operator
   confirmation.
6. Only after the above is trustworthy: Fedora systemd scheduling live,
   MCP/interactive review access, benchmark simulation, postmortems.

**First live-report exit criteria:** historical inputs sourced and
snapshotted for every tracked asset, BTC has an independent assessment,
sentiment provenance present or explicitly unavailable with reasons, all
schema/business checks pass, and an operator reviews and confirms the
frozen artifact. No roadmap item authorizes trade execution.

## 21. Key documents (for a rebuild, read in this order)

1. This document (overview + rebuild spec).
2. `INVESTMENT_DECISION_SYSTEM.md` — the long-range design spec (more
   narrative detail on philosophy/policy than this document carries).
3. `schemas/frozen-report.schema.json` — the actual data contract.
4. `docs/wiki/` — per-module implementation reference
   (`architecture.md`, `configuration.md`, `indicators.md`, `reports.md`,
   `snapshots.md`, `ingestion.md`, `roadmap.md`, `changelog.md` for
   dated history of every material behavior change).
5. `docs/candidates/BTCB2.md` — the one worked example of the crypto
   asset inclusion gate in practice.
6. `docs/archive/` — historical two-agent build coordination log and a
   consolidated design-doc review; useful context, not current policy.
