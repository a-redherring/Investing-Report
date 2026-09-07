# Changelog

Dated log of material changes to code behavior (not every commit — just things a
future reader would otherwise have to discover by diffing). Newest first.

## 2026-09-07 — operator_thesis removed entirely; BTCB2 criteria 4/5/6 pass

Operator judgment, superseding the same-day rename below: the
`operator_thesis`/"stated belief" concept never played a real part in
anything and is irrelevant — removed entirely rather than kept under a
different name.

- **`bitcoin.blake2b_gate.operator_thesis` removed from the schema**
  (`schemas/frozen-report.schema.json`) — the whole optional sub-object,
  not just its disclosure string. `reports/practice/P-001.example.json` no
  longer has the field at all (previously `null`).
- **`tests/test_schema.py`**: removed all 5 `operator_thesis`-specific
  tests and the `DISCLOSURE` constant; added one regression test
  (`test_blake2b_gate_rejects_operator_thesis_as_an_unknown_field`) that
  locks in the removal so it can't quietly reappear as schema drift. Net
  69 → 65 tests (still all passing).
- Removed the "Operator thesis" section from `docs/wiki/reports.md`
  entirely, and the corresponding cross-references from
  `docs/wiki/configuration.md`, `docs/wiki/ingestion.md`, and
  `INVESTMENT_DECISION_SYSTEM.md`'s crypto asset inclusion gate (criterion
  6 no longer references the field at all — it now just requires a written
  thesis and invalidation conditions, full stop).
- Historical changelog entries below (2026-09-04) still describe
  `operator_thesis` as built, and `docs/archive/agent-handoff-2026-09-04.md`
  still quotes its original disclosure text verbatim — both left untouched
  as accurate record of what was true at the time; the field has since been
  removed.
- **`docs/candidates/BTCB2.md` criteria 4 and 5 marked PASS**: the operator
  personally verified that existing Bitcoin wallet software works
  identically for BTCB2 (same fork, only the PoW algorithm changed) and
  that they run their own independent BLAKE2b node — recorded as operator
  attestation rather than a public source, since a custody/verification
  setup is inherently a private fact this project's own rules keep out of
  public artifacts (unlike criteria 1-3, which should stay independently,
  publicly checkable).
- **Criterion 6 marked PASS**: its actual requirement is that a written
  thesis and explicit invalidation conditions *exist* — a plausibility/
  risk-modelling exercise, not proof BTCB2 will succeed — and that's met.
  Reframed as an ongoing check rather than a one-time pass: each future
  report should test current conditions against the six invalidation
  conditions and flag if any are met, which would put the thesis back into
  question rather than requiring a rewrite from scratch.
- Net effect: criteria 4/5/6 now pass, 1 still fails (~1 week old, needs
  ≥3 months), 2/3 remain unsourced — BTCB2 is still short of the full gate,
  but materially closer than the previous all-`TODO` state.

## 2026-09-07 — operator_thesis disclosure reworded; BTCB2 thesis trimmed

Two follow-up cleanups to the same-day work below.

- **`bitcoin.blake2b_gate.operator_thesis.disclosure`'s schema `const`
  reworded** from *"Operator's personal conviction; unverified, and does
  not affect blake2b_gate.status or any hard gate."* to *"Operator's own
  stated belief; unverified, and does not affect blake2b_gate.status or any
  hard gate."* at operator request — same meaning (unverified,
  gate-status-inert), different wording. Updated everywhere this string is
  enforced or quoted: `schemas/frozen-report.schema.json`,
  `tests/test_schema.py`'s `DISCLOSURE` constant (3 tests reference it by
  variable, so one change propagates), `docs/wiki/reports.md`, and
  `INVESTMENT_DECISION_SYSTEM.md`. `reports/practice/P-001.example.json`
  needed no change (`operator_thesis` is `null` there). Historical
  changelog entries and the archived `docs/archive/agent-handoff-2026-09-04.md`
  keep the original string verbatim, since they're accurate historical
  record of what the field said at the time, not live documentation.
  Full suite: 69 passed.
- **Trimmed `docs/candidates/BTCB2.md`**: dropped the Sybil-node-support
  allegation aside entirely (no evidence either direction, didn't change
  any conclusion — a dead end, not a data point) and condensed the
  whitepaper-citation discussion from a full argument-section paragraph to
  a single closed line in Background (it's neutral — neither supports nor
  opposes the thesis — so it doesn't belong in the list of live,
  contributing arguments).

## 2026-09-07 — BTCB2 candidate thesis (criterion 6) drafted

Wrote `docs/candidates/BTCB2.md`'s criterion-6 ("Defined thesis and risk
model") section, following a research conversation covering: the real
BIP-110/BLAKE2b origin story (Bitcoin Core v30's OP_RETURN limit removal,
BIP-110's failed anti-spam/anti-CSAM soft fork, the Knots-led BLAKE2b hard
fork, Luke Dashjr's confirmed 2026-08-29 resignation from Ocean Mining);
current mining-pool concentration data (Foundry+AntPool, Nakamoto
Coefficient); real precedent for compliance-driven transaction filtering
(F2Pool, Marathon 2021); documented CSAM content already found on-chain via
academic research; and evidence on Bitcoin's decentralization
culture (self-custody vs. node-running as distinct metrics, Michael
Saylor's public shift toward endorsing Solana/Ethereum infrastructure,
node-counter infrastructure neglect).

- **Verified and rejected as a citation**: the claim that Nakamoto's
  whitepaper mandates a PoW change when regulated agencies hold majority
  hashrate — checked directly against the whitepaper text, no such clause
  exists, and "honest nodes" is a purely behavioral (rule-following)
  definition indifferent to operator identity/regulatory status. Recorded
  as neutral (neither supports nor opposes the thesis), not as evidence
  against it.
- **Kept open rather than resolved**: whether economic-majority actors
  (exchanges, custodians, index/ETF providers) would actually reject a
  majority-hashrate rule change (e.g. demurrage) rather than simply
  relisting whichever chain the market treats as "real BTC" — this
  undercuts the standard "nodes would just reject it" counter-argument and
  is flagged for further evidence, not treated as settled either way.
- **Reweighted per operator direction**: censorship-driven confirmation
  delay treated as potentially functionally equivalent to a block (not
  dismissed as merely inconvenient) if compliance pressure extends beyond
  the top 2 mining pools; CSAM risk treated as a moral/ethical priority that
  isn't resolved by legal experts' "overblown" probability-of-prosecution
  framing; node-running (not aggregate self-custody figures) treated as the
  load-bearing decentralization-culture metric, since self-custody without
  independent validation still relies on trusting a third party per the
  whitepaper's own Simplified Payment Verification section.
- **New**: six explicit, falsifiable invalidation conditions (mining
  decentralization trend, a real tested instance of economic-majority
  rejection of a bad rule change, Stratum V2 preventing censorship in
  practice, node-metric recovery, durable CSAM mitigation on mainline
  Bitcoin, or BTCB2 failing to gain adoption despite persistent
  vulnerabilities).
- Explicitly scoped out: Neoxa Exchange venue/custody risk (missing-deposit
  and scam reports) — removed from this write-up pending better-sourced
  evidence; criteria 1-5's asset-status tracking is unaffected by and
  separate from this criterion-6 concept discussion.
- No code, schema, or config changes — documentation only.

## 2026-09-06 — BTCB2 reverted to candidate-only; single-agent development

Operator direction: proceed with a single coding agent (Claude Code) going
forward, and roll BTCB2 back to its original conservative design — tracked as
a candidate the system is ready to add once it clears a decidable
"established" bar, not a configured universe asset.

- **`config/universe.yaml`**: removed the BTCB2 row. The universe is back to
  IVV, NDQ, VAS, VGS, IZZ, VAE, GOLD, BTC, CASH — no cryptocurrency other than
  BTC.
- **`config/model-v1.1.yaml` → `config/model-v1.0.yaml`**, `model_version`
  `"1.1"` → `"1.0"`. The only substantive content of v1.1 was BTCB2's
  inclusion; reverting that made v1.0 the accurate version again.
  `src/investment_system/config.py`'s hardcoded marker filename and
  `tests/test_config.py`'s assertions updated to match.
- **`INVESTMENT_DECISION_SYSTEM.md`**: removed BTCB2 from `config/universe.yaml`
  and reverted the model to v1.0 (below), and replaced the six vague
  BLAKE2b-gate bullets ("sufficiently established and secure", etc.) with a
  concrete, decidable **crypto asset inclusion gate** — generalized beyond
  BLAKE2b-specifically, since there's no blanket ban on non-BTC
  cryptocurrencies, only the closed-universe process plus this gate. BTCB2
  is currently the only candidate under consideration, tracked in a new
  "Candidate assets not yet in the universe" table. Split the old combined
  "Bitcoin BLAKE2b monitoring and BTCB2 eligibility" section into two: an
  unconditional BLAKE2b-fork monitoring subsection, and the crypto asset
  inclusion gate. Final gate, after two rounds of operator review:
  - **Operational maturity**: mainnet live ≥3 months, no unresolved
    consensus-halting incident during that period. (Initially drafted at 24
    months; shortened to 3 on operator direction.)
  - **Liquidity**: ≥US$250,000 trailing-30-day average daily volume across
    ≥2 independent, non-affiliated exchanges — single-venue volume never
    qualifies.
  - **Price discovery**: ≥2 independent venues quote the reference pair,
    <5% divergence between them at report time.
  - **Custody**: self-custody via open-source wallet software, or a
    recognized third-party custodian/hardware wallet — exchange-only
    custody doesn't count.
  - **Independent verifiability**: a public block explorer and node
    software independent of any single exchange.
  - **Defined thesis and risk model**: a written, dated investment thesis
    and explicit invalidation conditions, distinct from the operator's own
    stated-belief disclosure.

  A draft seventh criterion — an independent published security/code audit
  — was proposed and then **removed by operator decision** as impractical
  for this asset; the doc records that removal explicitly rather than
  silently dropping it. All six must be demonstrated, with sources, across
  ≥4 consecutive Monday reports before a new model-version change may
  propose re-adding BTCB2 (or any future crypto candidate). Framed the
  thresholds as a working default the operator can recalibrate — including
  removing a criterion, as just happened — rather than a claim of
  precision. Updated every other BTCB2/model-version mention in the document
  (tracked-universe table, BTC/BTCB2 assessment section, "Decisions already
  made", open question #11, the illustrative "Full universe" example row) to
  match.
- **Wiki**: `docs/wiki/architecture.md`, `configuration.md`, `roadmap.md`,
  `reports.md`, `ingestion.md`, and the root `README.md` updated to stop
  describing BTCB2 as included, and to point at the establishment gate
  instead.
- **New `docs/candidates/BTCB2.md`**: no report-generation step exists yet to
  record progress against the gate's six criteria, so this file is, for now,
  the one place that happens — one section per criterion with a
  status/evidence/last-reviewed placeholder, including the written thesis
  and invalidation conditions criterion 6 requires. Created entirely as
  `TODO` placeholders except custody and independent verifiability, marked
  "operator states satisfied — needs sourcing" per the operator's own
  statement; nothing in it is treated as verified until sourced here and
  reproduced in an actual Monday report. Linked from
  `INVESTMENT_DECISION_SYSTEM.md`'s candidate table and establishment-gate
  section, and from `docs/wiki/architecture.md`'s file listing.
- **Single-agent development**: the earlier two-agent (Claude Code + Codex)
  build split has ended. Archived `docs/CLAUDE_CODE_HANDOFF.md` to
  `docs/archive/agent-handoff-2026-09-04.md` with a header marking it
  historical (not a live coordination doc). Consolidated the two
  independently-written, confusingly-similarly-named design-doc reviews
  (`docs/design-doc-review-2026-09-04.md` and
  `docs/design-document-review-2026-09-04.md`, both from 2026-09-04) into one
  file, `docs/archive/design-review-2026-09-04.md`, preserving both sets of
  findings and adding a resolution-status note for what this change
  superseded. Updated all links in `README.md`, `docs/wiki/README.md`, and
  `docs/wiki/reports.md` accordingly.
- Full suite: 69 passed (`python -m pytest -q`, clean venv). No schema or
  validation-rule changes — this was universe/config/documentation only.

## 2026-09-04 — public README, roadmap, and wiki synchronization

- Reworked the repository README as the front-facing entry point, including
  Fedora quick start, current scope, secrets guidance, and links to operations
  and coordination docs.
- Added the [Roadmap](roadmap.md) with completed foundations, the next build
  sequence, and first-live-report exit criteria.
- Corrected wiki status claims for Finnhub quote ingestion and write-once
  report freezing, and reconciled the design-review links/status notes.

## 2026-09-04 — Finnhub quote ingestion (Claude Code's half of the parallel split)

Per the handoff's "Active parallel work split": built the Finnhub half while
Codex builds Fedora deployment. Scope stuck exactly to what was assigned —
`src/investment_system/ingestion/`, `config/data-sources.yaml`, Finnhub
fixtures/tests, snapshot integration. Did not touch `deploy/`, `.env.example`,
`scripts/`, or `docs/fedora-deployment.md`.

- **New `ingestion/` package**: `errors.py` (a provider-agnostic
  `IngestionError` hierarchy: `IngestionConfigError`, `IngestionRequestError`,
  `IngestionRateLimitError`, `IngestionResponseError`, `IngestionStaleDataError`),
  `data_sources.py` (loads `config/data-sources.yaml`), `finnhub.py`
  (`fetch_quote()`).
- Every required behavior from the handoff assignment, verified with a test
  each: reads `FINNHUB_API_KEY` from the environment and fails closed if unset
  (never calling the transport); sends the key as an `X-Finnhub-Token` header,
  never in the URL; a transport-level failure (rate limit included) raises a
  distinct error; a malformed, incomplete, or Finnhub's-all-zero
  "unrecognized symbol" response raises and is still snapshotted first (raw
  evidence preserved even on rejection); a quote older than
  `max_quote_age_seconds` (default 3600s) raises, also post-snapshot; no test
  touches the network — the HTTP transport is dependency-injected and every
  test supplies a fake.
- **Verified against the real API, not just fixtures**: ran
  `investment-system fetch-quote AAPL` with a deliberately fake key against
  the actual `finnhub.io` endpoint — got back a real HTTP 401, surfaced as a
  clean `IngestionRequestError` with exit code 1. Confirms the request-
  building/header/error-handling path end to end, not just against canned
  responses.
- New CLI: `investment-system fetch-quote <symbol> [--db PATH]` — the
  "deterministic callable/CLI boundary" the handoff's integration-boundary
  note asked for, so a scheduler can invoke it by exit code without importing
  Finnhub internals. Reads `INVESTMENT_SYSTEM_SNAPSHOT_DB` if `--db` isn't
  given (falls back to the existing default). **Deliberately not added to
  `make smoke`** — it needs a real API key and network access, which smoke
  tests shouldn't depend on.
- No new dependency: built on stdlib `urllib`, not `requests` — wasn't needed.
- **What's explicitly not built**: historical/weekly-candle ingestion (a
  single quote can't feed `indicators.calculate()`, which needs a time
  series — deferred rather than guessed at, since Finnhub's historical-candle
  access varies by pricing tier and that hasn't been confirmed); anything for
  BTCB2/Neoxa (Finnhub doesn't cover that exchange); nothing calls
  `fetch-quote` automatically.
- 14 new tests (`tests/test_ingestion_finnhub.py` + 4 offline fixtures under
  `tests/fixtures/finnhub/`). Full suite: 69 passed.
- New wiki page [Ingestion](ingestion.md); updated [Architecture](architecture.md)
  (including a stray broken code fence from an earlier edit, and the
  now-inaccurate blanket "no network calls" claim — the deterministic core
  still makes none, but this one opt-in adapter does).

## 2026-09-04 — Fedora deployment baseline

- Added a Fedora-only offline healthcheck, `.env.example`, and systemd service
  and timer templates for the future Monday runner.
- Templates are intentionally not enabled because `monday-run` and the live
  ingestion/report pipeline do not exist yet.

## 2026-09-04 — append-only report freezing

- Added `reports.py` and `freeze-report`: explicit-confirmation report
  validation, canonical JSON serialization, SHA-256 sidecar hashes, and
  write-once report IDs.
- Added regression tests for confirmation, idempotency, changed-content
  rejection, and hash output.

## 2026-09-04 — BTCB2 added to universe

- Added BTCB2 to `config/universe.yaml` as a non-core crypto asset with the
  `BTCB2_USDC` Neoxa Exchange reference pair.
- Bumped the model configuration from v1.0 to v1.1 and recorded the operator's
  authorization and pending independent verification in the asset metadata.
- This is a universe/configuration change only; it does not create a buy/sell
  recommendation or assert that the venue price is fair value.

## 2026-09-04 — operator-thesis field + a real jsonschema format-checking gap fixed

The operator asked for a Neoxa-listed BLAKE2b BTC development to be "fully
integrated ... treating it as much the same as possible as bitcoin," including
an automated buy/sell recommendation, on the strength of a personal belief that
it will "one day become the real bitcoin." Declined the buy/sell-recommendation
and universe-membership parts of that request; built the part that fits the
system's own rules. See the conversation for the full reasoning; short version:

- The design doc's BLAKE2b gate exists specifically to prevent an unverified
  BLAKE2b-related asset from entering the tradable universe on conviction
  alone — "this gate is not an endorsement of a fork or asset," and hard gates
  "cannot be silently overridden" by an overlay or a thesis.
- No ranking/scoring engine exists for **any** asset yet (agreed and recorded
  in every handoff entry above) — so building one now, for the single asset
  with zero verified fundamentals, would be the least-justified place to start.
- I have no independently verifiable information about Neoxa's legitimacy,
  liquidity, or security, and won't fabricate or fetch unvetted price data to
  feed a "recommendation."

What was built instead:

- **`bitcoin.blake2b_gate.operator_thesis`** (optional, nullable): records the
  operator's stated belief, dated, with a schema-`const`-enforced disclosure
  string that can never be stripped — the thesis is visible in every report
  and gets graded at the design doc's 4/13/26/52-week postmortems, but cannot
  itself flip `blake2b_gate.status` or any BTC assessment confidence. See
  [Reports and validation](reports.md#operator-thesis-bitcoinblake2b_gateoperator_thesis).
- Confirmed and documented (with a new test,
  `test_technical_signals_treat_every_asset_symbol_identically`) that
  `calculate_signals()` already treats every asset symbol identically — no
  universe allowlist, no special-casing — so "same technical treatment as
  other assets" was already true and needed no code change. The asset itself
  still does **not** go into `config/universe.yaml` (that's what the BLAKE2b
  gate governs) unless and until it independently clears the gate.
- **Found and fixed a real bug while adding tests for the above**: `jsonschema`
  does not enforce `"format": "date-time"`/`"format": "date"` at all unless
  the optional format-validator plugins are installed — `schema.py` was
  already passing a `FormatChecker()` (Codex's `test_schema_enforces_datetime_formats_and_btc_direction`
  caught this), but the checker had nothing registered for `date-time`
  without them. Every `date-time`/`date` field in the schema (`generated_at`,
  `data_cutoff`, `decision_date`, `checked_at`, `effective_at`,
  `retrieved_at`, `recorded_at`, ...) was silently unvalidated until now.
  Fixed by depending on `jsonschema[format]` instead of bare `jsonschema`.
- 6 new tests for `operator_thesis` (default-null validates, well-formed
  validates, wrong disclosure text rejected, missing required field rejected,
  status/confidence unaffected by a thesis) + 1 for symbol-agnostic technical
  signals. Full suite: 55 passed.

## 2026-09-04 — config/schema portability + snapshot store

Assigned split: Claude Code took the two remaining unclaimed items from the
handoff (config portability, provenance/snapshot storage); Codex took BTC/
sentiment — see the "validation and practice-report contract" entry below,
which already records the bitcoin/sentiment schema additions.

- **Config/schema path resolution is now portable.** `config.resolve_repo_root()`
  checks the `INVESTMENT_SYSTEM_CONFIG_DIR` env var (config only), then a
  `config/`/`schemas/` directory under cwd or its parents, then the path
  relative to the installed package — resolved fresh on every call, not baked
  into a function-default at import time as before. Verified against a real
  built wheel installed in a throwaway venv and run from an unrelated cwd: now
  fails closed with an actionable message (was previously either wrong or an
  unhelpful crash), and works correctly once `INVESTMENT_SYSTEM_CONFIG_DIR` is
  set. Removed `config.REPO_ROOT`/`config.CONFIG_DIR` (only `schema.py`
  depended on them, updated in the same change) in favor of
  `resolve_repo_root()`. See
  [Configuration](configuration.md#portability-non-editable-installs).
- **Added `snapshots.py` (`SnapshotStore`)**: an append-only, SQLite-backed,
  content-identified store for raw input snapshots — the "immutable raw
  snapshot storage" from the design doc's Phase 1, decoupled from any specific
  data source (none exists yet). Identity is `sha256(source + retrieved_at +
  content)`: identical inputs are a no-op, changed content is always a new
  row, never an overwrite. New CLI: `snapshot-save`/`snapshot-get`/
  `snapshot-list`. See [Snapshots](snapshots.md).
- Added 16 new tests (7 for config path resolution, 9 for `SnapshotStore`).
  Full suite: 45 passed (`python -m pytest -q`, verified in a clean venv).
- Did **not** wire the snapshot store into `calculate_signals()` or the
  report schema's `input_snapshot_id` — no ingestion step exists yet to call
  it automatically; that's future work once one does.

## 2026-09-04 — RSI switched to Wilder's smoothing

Picked up from `docs/CLAUDE_CODE_HANDOFF.md`'s "decide whether production RSI is
Cutler's or Wilder's, then add a verified golden fixture."

- **`indicators.rsi()` now implements Wilder's smoothed RSI** instead of
  Cutler's plain trailing-average RSI. Decision rationale: Wilder's is what
  brokers and virtually every charting platform quote, so a value in a Monday
  report is now directly comparable to what a human sees on their own broker's
  chart — the entire point of a decision-support report. Formula independently
  confirmed against Wikipedia's "Relative strength index" article and
  macroption.com/rsi-calculation (both state the identical recurrence).
- **This is a behavior change, not just documentation**: RSI now depends on the
  *entire* price history passed in, not just the trailing `period + 1` values,
  and is order-dependent. Any code or report that assumed RSI could be
  recomputed from a truncated recent window alone must pass the full series.
  (Nothing in this repo did that assume that yet — no scoring/report layer
  consumes RSI besides the illustrative fixture.)
- Added `tests/test_indicators.py::test_rsi_matches_wilders_smoothing_formula`:
  a period=5 fixture with the seed average and every smoothing step traced by
  hand in a comment, independent of the implementation, then asserted against
  the code's actual output.
- Updated [Indicators](indicators.md#rsi-rsi-default-period-14) with the
  corrected formula and the source confirmation.
- Existing RSI edge-case tests (all-gains/all-losses/no-change) were unaffected
  by this change — they all use series of length exactly `period + 1`, where
  Wilder's seed average and Cutler's window average are identical (the
  smoothing recurrence only kicks in for later observations).

## 2026-09-04 — report validator (schema + business rules)

Picked up from `docs/CLAUDE_CODE_HANDOFF.md`'s first suggested next-work item:
"add an internal report validator for unique contiguous ranks, complete universe
coverage, and practice/live date rules; keep JSON Schema as the structural
contract."

- Added `validation.validate_report()`: `report_id` pattern must match
  `report_kind` (schema alone accepts either pattern for either kind), `live`
  reports must fall on a Monday, `rankings[].rank` must be unique integers
  contiguous from 1, and (when `expected_assets` is given) every expected asset
  must appear in `rankings`.
- Added `schema.py`: loads `schemas/frozen-report.schema.json` and runs it
  through the `jsonschema` library (`schema_errors()`); added `jsonschema` as a
  dependency.
- Added `engine.validate_report()`: runs both the schema and the business rules
  together, defaulting `expected_assets` to the real `config/universe.yaml`.
  Confirmed `reports/practice/P-001.example.json` passes the schema and the
  business rules, and correctly fails universe-coverage (it's a one-asset
  illustrative fixture, not a full-universe report — expected).
- Added `investment-system validate-report <path> [--no-universe-check]` CLI
  command; exits 1 on any validation error.
- Added `[project.optional-dependencies] dev = ["pytest>=7.0"]` — the README's
  quick start ran `pytest` without it ever being declared as installable.
- New pages: [Reports and validation](reports.md). Updated
  [Architecture](architecture.md) with the new modules/CLI command/data flow.
- Test suite grew from Codex's 20 to 28 (added `tests/test_schema.py`, extended
  `tests/test_validation.py`).
- Deliberately did **not** build a report-generating/draft-builder step, a
  scoring/ranking engine, or BTC/sentiment schema fields — per the handoff
  note's explicit "do not build ranking or live-data ingestion until the
  model-v1.0 open questions are resolved."

## 2026-09-04 — validation and practice-report contract

- Added fail-closed validation for missing fields, malformed dates, duplicate
  observations, non-finite/non-positive prices, and source-order date warnings.
- Added the initial frozen-report JSON Schema and an illustrative P-001 practice
  artifact. No live report is created.
- Added `docs/CLAUDE_CODE_HANDOFF.md` as the shared agent coordination channel.
- Added generated-package metadata to `.gitignore`.
- Added required source-agnostic Bitcoin and equity/crypto sentiment sections
  with explicit unavailable states and provenance fields. No live source or
  recommendation is implied.

## 2026-09-04

- Hardened report validation: malformed rankings now return structured errors,
  JSON Schema date/time formats are enforced, BTC BUY/SELL decision enums are
  direction-specific, SQLite snapshot rows reject direct updates/deletes, and
  reports can optionally verify `input_snapshot_id` against a snapshot DB.

- **Wired `config/*.yaml` into the engine.** `config.py` (new) loads
  `model-v1.0.yaml` and `universe.yaml`. `engine.cost_table()` now derives its
  brokerage minimum/rate/qualifying-buy limit from the loaded config instead of
  hardcoded literals; `engine.config_snapshot()` and `investment-system config`
  expose the parsed values for inspection. Added `pyyaml` as a dependency.
  See [Configuration](configuration.md).
- **Added `Mixed` trend label and MA slope.** `indicators.py` now computes
  `slope_50w`/`slope_200w` (rising/falling/flat vs. 4 weeks earlier) and
  `_classify_trend()` can emit `Mixed` when price and long-term MA structure
  disagree (golden/death cross intact against the current price position).
  Previously the code could only emit Strong/plain Uptrend/Downtrend or
  `Insufficient Data`, missing the `Mixed` label the design doc requires. See
  [Indicators](indicators.md#trend-label-_classify_trend).
- **`engine.load_prices()` now rejects duplicate `(asset, date)` rows** instead of
  silently keeping both (previously they'd both land in the sorted series and
  skew every moving average / RSI / MACD window that included them).
- **`engine.cost_table()` no longer computes `asx_brokerage()` twice per row** —
  it computes the fee once and derives drag from it, using `costs.asx_brokerage`
  directly (the existing `costs.brokerage_drag` was already redundant with this
  and remains available as a standalone pure helper).
- **Documented that `rsi()` is Cutler's RSI**, not Wilder's smoothing — this was
  already the implemented behavior, just previously undocumented. See
  [Indicators](indicators.md#rsi-rsi-default-period-14).
- Test suite grew from 4 to 14 tests: stretch-label boundaries, RSI edge cases
  (all-gains/all-losses/flat/insufficient-history), slope's extra lookback
  requirement, Strong Uptrend/Downtrend and both `Mixed` cases, duplicate-date
  rejection, and config loading/wiring (both the committed YAML values and a
  synthetic `ModelConfig` fixture).
- Created this wiki (`docs/wiki/`) as the maintained reference for current
  code behavior, separate from the long-range design spec.

## Baseline (prior to this entry)

Initial runnable slice: `indicators.py` (SMA/EMA/RSI/MACD, stretch/trend labels
without `Mixed`), `costs.py` (ASX brokerage fee formula), `engine.py` (CSV loading
+ signal calculation + fee table with hardcoded fee constants), `cli.py`
(`signals`/`costs` commands). No config wiring, no slope, no `Mixed` label.
