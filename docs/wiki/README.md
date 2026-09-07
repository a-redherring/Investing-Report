# Wiki home

This is the maintained reference for the code in this repository: what exists today,
how it fits together, and what each config value and indicator actually does. It is
separate from [`INVESTMENT_DECISION_SYSTEM.md`](../../INVESTMENT_DECISION_SYSTEM.md),
which is the long-range design spec for the full Monday decision system (most of it
not yet built). This wiki documents current behavior and clearly labels planned
work.

## Pages

- [Architecture](architecture.md) — repository layout, module responsibilities, what's
  built vs. still a design placeholder.
- [Configuration](configuration.md) — every field in `config/*.yaml`, what it controls,
  and how to change it.
- [Indicators](indicators.md) — exact formulas, thresholds, and edge-case behaviour for
  every indicator/label the engine computes.
- [Reports and validation](reports.md) — the report JSON Schema, the cross-field
  business rules on top of it, and what's deliberately not built yet.
- [Snapshots](snapshots.md) — the append-only, provenance-bearing raw-input
  storage primitive, decoupled from any specific data source.
- [Ingestion](ingestion.md) — the Finnhub quote adapter, the only code in this
  repository that makes a real network call, and the fail-closed contract
  every future adapter should follow.
- [Roadmap](roadmap.md) — completed foundations, the next build sequence, and
  criteria for the first live report.
- [Changelog](changelog.md) — dated log of material changes to code behaviour.

This project is developed by a single coding agent (Claude Code). See
[`docs/archive/`](../archive/) for the earlier two-agent (Claude Code +
Codex) build history: [`agent-handoff-2026-09-04.md`](../archive/agent-handoff-2026-09-04.md)
(the coordination log from that phase, retained as historical record — not a
live coordination doc) and [`design-review-2026-09-04.md`](../archive/design-review-2026-09-04.md)
(a consolidated point-in-time audit of `INVESTMENT_DECISION_SYSTEM.md`, merging
what were originally two separately-written reviews). Their findings were used
to reconcile the design document; the file retains its original evidence and
points to what's since been resolved vs. still open.

## Keeping this wiki up to date

This wiki must be updated in the same change as any code it describes — not as a
follow-up. Concretely:

- Add/rename a config field → update [Configuration](configuration.md) in the same commit.
- Change an indicator formula, threshold, or add a new label → update
  [Indicators](indicators.md) in the same commit.
- Add/remove a module, CLI command, or change a responsibility boundary → update
  [Architecture](architecture.md) in the same commit.
- Any of the above → add a dated entry to [Changelog](changelog.md).
- Before merging a change to `src/` or `config/`, check whether these pages still
  describe the actual behavior. If unsure, run the code and confirm rather than
  guessing — these pages should reflect verified behavior, not intent.

A page that falls out of sync with the code is worse than no page — treat any
mismatch you find as a bug and fix the page immediately.
