# Reports and validation

There are two layers of validation for a report JSON document, deliberately kept
separate:

1. **Structural contract** — [`schemas/frozen-report.schema.json`](../../schemas/frozen-report.schema.json),
   a JSON Schema checked with the `jsonschema` library
   ([`schema.py`](../../src/investment_system/schema.py)). Field presence, types,
   and enums (e.g. `confidence` must be `high|medium|low|insufficient`).
2. **Cross-field business rules** — [`validation.validate_report()`](../../src/investment_system/validation.py),
   for relationships the schema can't express on its own:
   - `report_id` must match the pattern implied by `report_kind`: practice reports
     need `P-###`, live reports need `###`. The schema's regex alone accepts
     either pattern for either kind; this ties them together.
   - A `live` report's `decision_date` must fall on a Monday (per the design doc's
     Monday-only rule). Practice reports have no such constraint.
   - `rankings[].rank` values must be unique integers forming a contiguous
     sequence starting at 1 (no gaps, no duplicates).
   - Optionally (default on), every asset in `config/universe.yaml` must appear
     in `rankings[].asset` — full universe coverage.
   - `bitcoin` is required and must include separate BUY and SELL assessments
     plus the BLAKE2b gate. It may be `unavailable`, but unavailable BTC data
     requires explicit rationale/reason fields.
   - `sentiment` is required and must include separate equity and crypto Fear &
     Greed observations. Each observation records status, value/category,
     provider, effective time, and retrieval time. An unavailable observation
     must include a reason; an observed one must include all provenance fields.

`engine.validate_report(report, check_universe_coverage=True)` runs both layers
and returns a single `ValidationResult` (same `ValidationIssue`/`ValidationResult`
types `validate_prices` uses — `.valid`, `.errors`, `.warnings`).

`investment-system freeze-report` validates first, then writes canonical JSON
and a SHA-256 sidecar once. It requires `--confirm-freeze` and rejects changed
content for an existing report ID. This is an explicit operator action; no
command currently generates a report or freezes one automatically.

**BTCB2 is not in `config/universe.yaml`.** A prior model version (v1.1)
included it there by operator decision; that inclusion has been withdrawn and
the model reverted to v1.0. There is no blanket ban on non-BTC
cryptocurrencies — BTCB2 is tracked as the only candidate currently under
consideration, against `INVESTMENT_DECISION_SYSTEM.md`'s crypto asset
inclusion gate — it is not ranked, not sized, and not part of
`test_load_universe_reads_committed_yaml`'s expected symbol set. If it
independently clears the gate's six criteria, re-adding it (via a new
model-version change) still doesn't grant it an automatic trade signal: it
would go through the same symbol-agnostic technical engine and three-layer
model as every other asset, plus its own venue/liquidity/security overlay.

## Using it

```bash
investment-system validate-report reports/practice/P-001.example.json
investment-system validate-report reports/practice/P-001.example.json --no-universe-check
```

The command prints `{"valid": ..., "errors": [...], "warnings": [...]}` and exits
`1` if invalid — safe to use as a CI/pre-freeze gate once a report-generation
step exists.

## What's NOT here yet

- Nothing *generates* a report. `reports/practice/P-001.example.json` is a
  hand-written illustrative fixture (see its own `quality_control.warnings`) —
  there is no ranking engine, scoring layer, or draft-report builder. Building
  one is explicitly deferred until the model-v1.0 open questions in
  [`INVESTMENT_DECISION_SYSTEM.md`](../../INVESTMENT_DECISION_SYSTEM.md#current-open-questions)
  are resolved (weights, thresholds, hard gates).
- BTC BUY/SELL and sentiment sections exist as a source-agnostic contract.
  `ingestion.alternative_me`/`ingestion.cnn_fear_greed` can now fetch a valid
  `sentimentObservation` for each of `crypto_fear_greed`/`equity_fear_greed`
  (see [Ingestion](ingestion.md)), but no report-generation step exists yet
  to call them and assemble a report — the practice report still records
  both as explicitly unavailable. BTC BUY/SELL has no adapter at all (the
  Finnhub adapter fetches only single quotes). Assessment rules for how a
  sentiment reading modifies a BTC/ranking decision remain open, and BLAKE2b
  semantics remain open.
- Report freezing is implemented, but report generation is not. Snapshot
  storage and frozen-report artifacts are both append-only and integrity-
  hashed; neither is populated automatically by a scheduled pipeline yet.

## Adding a field to the report contract

1. Add it to `schemas/frozen-report.schema.json` (keep `additionalProperties: false`
   sections honest — don't let stray fields silently pass).
2. If it introduces a new cross-field relationship, add a rule to
   `validation.validate_report()`.
3. Update `reports/practice/P-001.example.json` so it still validates.
4. Add tests in `tests/test_schema.py` / `tests/test_validation.py`.
5. Update this page and add a [Changelog](changelog.md) entry.
