# Architecture

## What's actually built

```text
config/
  model-v1.0.yaml     Brokerage + cash-yield parameters for the current model version
  universe.yaml        Tracked asset list (BTCB2 excluded pending its establishment gate)
src/investment_system/
  config.py            Loads and type-checks the YAML config files above
  indicators.py         SMA/EMA/RSI/MACD, stretch/trend classification, MA slope
  costs.py              ASX brokerage fee calculation (pure function, no I/O)
  validation.py         Fail-closed CSV/report input validation and structured issues
  schema.py              Loads schemas/frozen-report.schema.json, runs JSON Schema
                         validation via the jsonschema library
  snapshots.py           Append-only SQLite store for raw input snapshots
                         (SnapshotStore) — provenance, not any specific data source
  reports.py             Canonical JSON report validation, hashing, and write-once freeze
  ingestion/              Live market-data adapters (Finnhub quotes, Yahoo weekly candles)
    errors.py              Shared IngestionError hierarchy
    data_sources.py         Loads config/data-sources.yaml (FinnhubConfig, YahooConfig)
    finnhub.py              fetch_quote(): fetch, snapshot, validate — see ingestion.md
    candles.py               WeeklyBar: the shared weekly-price-bar contract every
                             historical adapter produces
    yahoo.py                fetch_weekly_history(): fetch, snapshot, validate weekly
                             OHLC history — see ingestion.md for two real data-quality
                             bugs found and fixed here (range="max" coarsening,
                             corrupted IVV.AX history)
  engine.py             CSV loading, wires indicators.py + config.py together,
                         exposes calculate_signals() / cost_table() / config_snapshot()
                         / validate_report()
  cli.py                 `investment-system signals|costs|config|validate-report|
                         snapshot-save|snapshot-get|snapshot-list|fetch-quote|
                         fetch-history` commands
config/data-sources.yaml  Finnhub base URL/API-key env var/timeouts; Yahoo base URL/User-Agent/timeout
tests/                  Unit tests for every module above, plus tests/fixtures/prices.csv
                         and tests/fixtures/finnhub/, tests/fixtures/yahoo/ (offline
                         response fixtures for each ingestion adapter)
schemas/                First structural contract for frozen practice/live reports
reports/practice/       Illustrative schema-shaped practice artifact only
data/                   snapshots.sqlite3 lives here by default (gitignored)
deploy/systemd/         Fedora service/timer templates (not enabled yet)
scripts/                Fedora offline healthcheck
docs/candidates/        Crypto-asset-inclusion-gate tracking per candidate
                         (currently: BTCB2.md) — not code, not report data;
                         see INVESTMENT_DECISION_SYSTEM.md's establishment gate
```

The deterministic core (`indicators.py`, `costs.py`, `engine.py`'s CSV path,
`validation.py`, `schema.py`, `reports.py`) makes no network calls and never
will on its own — feed it a CSV/JSON, get the same output every time. As of
`ingestion/`, the repository *also* has two opt-in adapters that make a real
network call: `investment-system fetch-quote <symbol>` (requires
`FINNHUB_API_KEY`) and `investment-system fetch-history <asset>` (Yahoo
Finance, no key needed) — both only run when explicitly invoked. Nothing
calls either automatically; nothing in the deterministic core depends on
them existing. `fetch-history`'s output CSV, though, plugs directly into the
existing CSV pipeline below with no code change — see
[Data flow](#data-flow) and [Ingestion](ingestion.md).

## Data flow

```text
CSV (asset,date,close)
  -> engine.load_prices()        groups by asset, sorts by date, rejects duplicate
                                   (asset, date) rows and invalid prices
  -> indicators.calculate()      one TechnicalSnapshot per asset
  -> engine.calculate_signals()  dict of asset -> snapshot fields, for CLI/JSON output

config/*.yaml
  -> config.load_model_config()  ModelConfig (brokerage terms, cash yield)
  -> config.load_universe()      list of tracked assets
  -> engine.cost_table()         fee schedule for the 999/2000/4000 sizing tiers,
                                   driven by the loaded ModelConfig
  -> engine.config_snapshot()    what `investment-system config` prints

Report JSON (e.g. reports/practice/*.json)
  -> schema.schema_errors()      structural violations against schemas/frozen-report.schema.json
  -> validation.validate_report()  cross-field rules the schema can't express: report_id
                                     pattern must match report_kind, live reports must fall
                                     on a Monday, rankings must have unique contiguous ranks
                                     starting at 1; malformed rankings are
                                     reported rather than raising
  -> engine.validate_report()    combines both, plus (by default) a check that every
                                   config/universe.yaml asset is present in rankings
                                 -> what `investment-system validate-report` prints/exits on;
                                    optional snapshot-db reference verification

Snapshot store (data/snapshots.sqlite3 by default)
  -> snapshots.SnapshotStore.save()  content-identified, append-only; same
                                       (source, retrieved_at, content) is a no-op,
                                       any change to content is a new row, never
                                       an overwrite
  -> investment-system snapshot-save/-get/-list

config/data-sources.yaml
  -> ingestion.data_sources.load_finnhub_config()  FinnhubConfig (base URL, API-key
                                                     env var name, timeout, max quote age)
  -> ingestion.finnhub.fetch_quote(symbol, snapshot_store=...)
       reads FINNHUB_API_KEY from the environment (fails closed if unset)
       -> HTTP GET with the key as a header, never the URL/query string
       -> snapshots the raw response FIRST (evidence preserved even on failure)
       -> then validates: parses JSON, checks required fields, rejects Finnhub's
          all-zero "unrecognized symbol" response, rejects a quote older than
          max_quote_age_seconds
  -> investment-system fetch-quote <symbol>  (exits 1 with a structured error on
                                               any IngestionError; never touches
                                               rankings, gates, or recommendations)

config/data-sources.yaml
  -> ingestion.data_sources.load_yahoo_config()  YahooConfig (base URL, User-Agent, timeout)
  -> ingestion.yahoo.fetch_weekly_history(symbol, snapshot_store=..., range_=...)
       -> HTTP GET to Yahoo's chart endpoint, no key needed
       -> snapshots the raw response FIRST (evidence preserved even on failure)
       -> then validates: parses JSON, drops in-progress/null bars, rejects any
          single-week move beyond a 5x/0.2x sanity bound (see ingestion.md)
       -> returns list[WeeklyBar] (date, close), the shared contract every
          historical adapter produces (ingestion.candles.WeeklyBar)
  -> investment-system fetch-history <asset>  writes data/history/<ASSET>.csv in the
                                               same asset,date,close shape load_prices()
                                               already reads -> feeds straight into
                                               investment-system signals with no other
                                               change; exits 1 with a structured error
                                               on any IngestionError; GOLD/CASH rejected
                                               outright (no configured provider mapping)
```

See [Reports and validation](reports.md) for the report contract,
[Snapshots](snapshots.md) for the provenance store, and
[Ingestion](ingestion.md) for the Finnhub adapter.

`config.py` and `schema.py` resolve `config/` and `schemas/` by checking, in
order: the `INVESTMENT_SYSTEM_CONFIG_DIR` environment variable (config only),
a directory under the current working directory or one of its parents (the
documented workflow — run from within a clone of this repo), then the path
relative to this installed package (works for an editable/source install
regardless of cwd). This makes them work for a non-editable wheel install too,
as long as either the env var is set or the command is run from within a repo
checkout — see [Configuration](configuration.md#portability-non-editable-installs).

## What's in the design doc but NOT built yet

[`INVESTMENT_DECISION_SYSTEM.md`](../../INVESTMENT_DECISION_SYSTEM.md) describes a much
larger system: fundamental/regime scoring, sentiment ingestion, BTC BUY/SELL
assessments, the MCP server, frozen JSON/Markdown reports, SQLite audit storage,
benchmark simulation, and postmortems. Almost none of that exists in `src/` yet
(the exceptions are the frozen-report write-once mechanism in `reports.py` and
the Finnhub/Yahoo adapters in `ingestion/`) — this repository is still
overwhelmingly the "Phase 1: deterministic data foundation" slice. Don't assume
any scoring/ranking/BTC-or-sentiment-provider behavior is implemented; check
`src/investment_system/` directly. `ingestion.finnhub.fetch_quote()` produces
one validated quote — it does not feed `indicators.calculate()`.
`ingestion.yahoo.fetch_weekly_history()` does feed it (via `fetch-history`'s
CSV output), but nothing calls either adapter automatically, and neither
touches rankings, gates, or recommendations.

## CLI

```bash
investment-system signals <path-to-weekly-csv.csv>   # per-asset TechnicalSnapshot as JSON
investment-system costs                               # fee schedule for A$999/2,000/4,000
investment-system config                              # parsed model config + universe, as JSON
investment-system validate-report <path-to-report.json> [--no-universe-check]
                                                       # schema + business-rule validation;
                                                       # exits 1 if invalid
investment-system snapshot-save <source> <path> [--retrieved-at ISO8601] [--metadata JSON] [--db PATH]
investment-system snapshot-get <snapshot_id> [--db PATH]
investment-system snapshot-list [--source NAME] [--db PATH]
investment-system fetch-quote <symbol>                 # requires FINNHUB_API_KEY; makes a
                                                        # real network call; exits 1 with a
                                                        # structured error on any failure
investment-system fetch-history <asset> [--range WINDOW] [--output-dir DIR]
                                                        # Yahoo Finance weekly history for
                                                        # IVV/NDQ/VAS/VGS/IZZ/VAE/GOLD/BTC only;
                                                        # writes data/history/<ASSET>.csv
```
