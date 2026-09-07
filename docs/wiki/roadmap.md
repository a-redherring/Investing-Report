# Roadmap

This roadmap describes the build order for the Monday Investment Decision
System. Status reflects the code in this repository, not the long-range design
specification alone.

## Complete foundation

- Model v1.0 configuration. (A prior v1.1 added BTCB2 as an operator-authorized
  universe asset; that inclusion was withdrawn and the model reverted — see
  [`INVESTMENT_DECISION_SYSTEM.md`](../../INVESTMENT_DECISION_SYSTEM.md#crypto-asset-inclusion-gate)'s
  establishment gate for what BTCB2 must clear before it can return.)
- Deterministic weekly indicators: moving averages, Wilder RSI, MACD, slopes,
  stretch, trend, and drawdown.
- ASX brokerage-cost calculations and strict CSV validation.
- Frozen-report JSON Schema plus cross-field business validation.
- Append-only, content-identified SQLite snapshots with provenance and raw
  Finnhub quote capture.
- Explicit-confirmation, write-once report freezing with SHA-256 sidecars.
- Fail-closed Finnhub single-quote adapter with offline tests.
- Fedora healthcheck and systemd service/timer templates. Templates remain
  disabled until the scheduled report pipeline exists.

## Next build sequence

1. Add provider historical-candle ingestion and a canonical weekly-price
   contract. Verify Finnhub plan/tier behavior before relying on its candle
   endpoint; never infer a weekly series from a single quote.
2. BTCB2/Neoxa adapter and venue/liquidity/security/custody overlay: **gated,
   not scheduled.** Do not build this until BTCB2 independently clears the
   design doc's establishment gate (operational maturity, multi-venue
   liquidity, price discovery, security review, custody, independent
   verifiability, defined thesis) and an operator authorizes a new
   model-version change to re-add it. Track gate status, not adapter work,
   until then.
3. Decide and document equity/crypto sentiment providers, freshness rules, and
   unavailable-state behavior.
4. Build deterministic feature assembly, scoring, ranking, and draft-report
   generation against the existing schema and practice fixture.
5. Add a `monday-run` orchestration command that snapshots inputs, validates
   freshness and universe coverage, writes a draft, and never freezes without
   explicit operator confirmation.

## Later, after the pipeline is trustworthy

- Fedora home-server systemd scheduling and operational alerting.
- Local STDIO MCP access from a Fedora desktop/Codex review workflow.
- Benchmark simulation, transaction-cost analysis, and 4/13/26/52-week
  postmortem records.
- Production-readiness review covering backups, retention, upgrades, and
  recovery from partial runs.

## First live-report exit criteria

Report #001 should not be called live until historical inputs for every tracked
asset are sourced and snapshotted, BTC has an independent assessment,
sentiment provenance is present or explicitly unavailable with reasons, all
schema/business checks pass, and an operator reviews and confirms the frozen
artifact. No roadmap item authorizes trade execution. BTCB2 is out of scope
for Report #001 until it clears the establishment gate.
