# Monday Investment Decision System

This repository is the runnable foundation for the design in
[`INVESTMENT_DECISION_SYSTEM.md`](INVESTMENT_DECISION_SYSTEM.md). It is a
research and education tool: it does not provide financial advice, place
trades, or publish an automated recommendation.

The current implementation is a deterministic technical-analysis and data-
provenance foundation. It supports Fedora desktop testing and is being shaped
for a Fedora home server. The long-range decision engine remains under
development; see the [roadmap](docs/wiki/roadmap.md).

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install -e '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/investment-system signals tests/fixtures/prices.csv
./scripts/fedora-healthcheck.sh
```

The healthcheck is offline. Two optional commands make real network calls:
`fetch-quote` (requires `FINNHUB_API_KEY`; fetches one Finnhub quote) and
`fetch-history` (no key needed; fetches weekly price history from Yahoo
Finance for IVV, NDQ, VAS, VGS, IZZ, VAE, and BTC). Both snapshot their raw
response in the local append-only SQLite store. Neither creates a
recommendation; `fetch-history`'s output CSV feeds straight into `signals`.

Useful commands:

```bash
.venv/bin/investment-system config
.venv/bin/investment-system costs
.venv/bin/investment-system validate-report reports/practice/P-001.example.json
.venv/bin/investment-system snapshot-list
FINNHUB_API_KEY=... .venv/bin/investment-system fetch-quote AAPL
.venv/bin/investment-system fetch-history IVV
```

## Current scope

The configured universe is IVV, NDQ, VAS, VGS, IZZ, VAE, GOLD, BTC, and CASH.
There's no blanket ban on other cryptocurrencies, but adding one requires
clearing a documented establishment gate (mainnet maturity, multi-venue
liquidity, security review, custody, independent verifiability, and a defined
thesis — see
[`INVESTMENT_DECISION_SYSTEM.md`](INVESTMENT_DECISION_SYSTEM.md#crypto-asset-inclusion-gate)).
BTCB2 is currently the only candidate under consideration, tracked pending
that gate; it is not in `config/universe.yaml`, not ranked, and not a buy
signal.

Implemented foundations include weekly indicator calculations, ASX brokerage
costs, strict price/report validation, schema validation, append-only
snapshots, explicit-confirmation report freezing, the Finnhub single-quote
adapter, and Yahoo Finance weekly-history ingestion for 7 of 9 universe assets
(see the [roadmap](docs/wiki/roadmap.md)). Gold's data vehicle, sentiment,
BTCB2/Neoxa ingestion, scoring, report generation, and scheduling are not yet
implemented.

Secrets belong in the process environment or an external server-side secrets
file. Do not commit `.env` files or API keys; `.env.example` documents names
only.

See the [wiki](docs/wiki/README.md) for the maintained implementation
reference, [Fedora deployment guide](docs/fedora-deployment.md) for the home
server operating model, and [`docs/archive/`](docs/archive/) for the earlier
two-agent (Claude Code + Codex) build history. Development now proceeds with
a single coding agent (Claude Code).

## Data format

CSV input must contain `asset,date,close`, with one row per completed weekly
observation. Prices should use the documented, consistently adjusted basis.
The engine fails when an asset lacks enough history for a requested indicator.
