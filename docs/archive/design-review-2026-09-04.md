# Design document review — 2026-09-04 (archived, consolidated)

> **Archived and merged 2026-09-06.** This file merges two independent
> point-in-time reviews of `INVESTMENT_DECISION_SYSTEM.md` written on the same
> day by Claude Code and Codex, during the earlier two-agent build split
> (which has since ended — see `docs/archive/agent-handoff-2026-09-04.md`).
> They were originally two separate files at confusingly similar paths
> (`design-doc-review-2026-09-04.md` vs. `design-document-review-2026-09-04.md`
> — a genuine accidental filename collision, not a deliberate fork) and were
> flagged for consolidation at the time; this is that consolidation. Findings
> are retained as an audit trail, not a live status page — check the current
> `INVESTMENT_DECISION_SYSTEM.md`, `docs/wiki/`, and tests for present
> behavior. In particular, everything below discussing BTCB2 as included in
> the universe under Model v1.1 is superseded: that inclusion was withdrawn
> on 2026-09-06, the model reverted to v1.0, and BTCB2 is now tracked only as
> a candidate pending its establishment gate.

Scope: `INVESTMENT_DECISION_SYSTEM.md` as it stood on 2026-09-04 (post BTCB2/
Model v1.1 additions). Reviewed for internal mistakes and redundancies — not a
review of the codebase itself. Findings are ordered worst first within each
reviewer's list. Verified claims are marked as such; everything else is a
reading of the document.

## Resolution status (as recorded when the reviews converged, 2026-09-04)

- Resolved in the design document at the time: Model v1.1/BTCB2 inclusion,
  repository-schema authority, current Finnhub quote scope, Fedora-only
  direction, and the first-report roadmap.
- Resolved in the implementation/docs at the time: the report-freeze
  mechanism was documented as implemented, and the wiki distinguished Finnhub
  quotes from the still-planned historical, sentiment, and BTCB2 adapters.
- Remaining at the time: the embedded conceptual example was explanatory
  rather than a schema fixture; the dedicated BTCB2 recommendation overlay
  and enforcement rules, automated report generation, and consolidation of
  repeated design prose were future work.
- **Since superseded (2026-09-06):** BTCB2 universe inclusion was withdrawn
  and the model reverted to v1.0. The "BTCB2 overlay/enforcement rules" item
  above is now gated behind BTCB2 clearing the establishment criteria in
  `INVESTMENT_DECISION_SYSTEM.md`, not scheduled work.

## Claude Code's findings

### 1. The illustrative JSON example is out of sync with the real schema (verified)

The "Structured frozen-report schema" section (`INVESTMENT_DECISION_SYSTEM.md`,
"Structured frozen-report schema") shows a `json` example that was run through
the actual validator (`investment_system.schema.schema_errors()`) and produces
**13 distinct violations** against `schemas/frozen-report.schema.json`:

- Four entire top-level sections don't exist in the real schema and would be
  rejected outright: `features`, `sources`, `selected_decision`, `report_hash`.
- `assumptions.btc_reference_basis_usd` isn't a real field.
- `bitcoin.buy_assessment`/`sell_assessment` are shown as plain strings
  (`"NO BUY"`, `"HOLD"`); the real schema requires objects shaped
  `{decision, confidence, rationale}`. The required `bitcoin.status` field is
  missing entirely from the example, and `cycle_prior`/`price_usd`/
  `gain_from_60000_basis_pct` aren't real properties of `bitcoin`.
- `rankings[]` items show `valuation`, `technical_stretch`, `trend`, `regime`,
  `waiting_risk`, `score` — **none of these exist in the real schema.** The
  actual `rankings[]` item only has `rank, asset, new_money_action,
  existing_position_action, confidence, hard_gates_passed, rationale`.
- `sentiment.*` is missing the required `status` and `retrieved_at` fields.
- `quality_control` shows `checks_passed`/`missing_fields`/`secret_scan_passed`
  — none real; the actual required field `validation_status` is missing.

The document's own "Document authority and maintenance" section states: *"When
they differ from the repository schema, the repository schema wins and this
document must be corrected in the same change."* This example was never
corrected as the schema evolved. As written, it would produce an invalid
report if followed literally instead of reading the schema directly.

**Reproduction:**

```bash
python3 -c "
from investment_system.schema import schema_errors
import json
example = json.load(open('/dev/stdin'))
for e in schema_errors(example): print(e)
"
```
(paste the doc's example JSON on stdin — or see the 13 errors listed above)

### 2. A present-tense claim overstated what was actually implemented

*"Bitcoin BLAKE2b monitoring and BTCB2 eligibility"* section stated (at the
time): *"Model v1.1 is an explicit operator-authorized exception that places
BTCB2 in the configured universe while **retaining** the six checks as
mandatory risk disclosures and **hard constraints** on confidence and
sizing."*

Checked `src/investment_system/validation.py` and
`schemas/frozen-report.schema.json` directly: neither had any BTCB2-specific
rule at the time. The document asserted something as currently true that
wasn't built. (Since superseded: BTCB2 is no longer in the universe at all.)

### 3. BTC BUY/SELL "allowed states" don't match the schema's actual enums

"Mandatory separate BTC and BTCB2 assessments" → BTC BUY lists: `BUY A$1,000
equivalent`, `BUY A$2,000 equivalent`, `BUY A$4,000 equivalent`, `WATCH`,
`NO BUY`. The real schema's `btcBuyAssessment.decision` enum is
`["BUY", "WATCH", "NO_BUY", "INSUFFICIENT_DATA"]` — no sizing distinction in
the enum at all, and `INSUFFICIENT_DATA` isn't mentioned in this section's
prose despite being required by, and actually used in,
`reports/practice/P-001.example.json`. Same gap for BTC SELL's allowed-states
list (missing `INSUFFICIENT_DATA`).

### 4. Redundancy: the "schema is authoritative" disclaimer is repeated in five places

Near-identical statements that the repository schema/code, not this document,
is the source of truth appear in:

1. "Document authority and maintenance" (the canonical statement)
2. "Technical stretch and trend" ("The exact implemented indicator contract is
   maintained in the repository's code/wiki...")
3. "Sentiment" ("The report schema is the canonical field contract...")
4. "Frozen reports and model versioning" ("The repository JSON Schema is the
   canonical structural contract...")
5. "Structured frozen-report schema" (the section's own intro and closing line)

Worth consolidating to the one canonical statement plus cross-references —
especially since, per finding #1, repeating the disclaimer hasn't actually
prevented the drift it's meant to guard against.

### 5. Minor naming inconsistency

The BTC-gain formula variable is `gain_from_reference_pct` ("BTC SELL"
section) but the JSON field shown for the same concept is
`gain_from_60000_basis_pct` ("Structured frozen-report schema"). Two names for
one concept, and neither is an actual field in the real schema (see #1).

### 6. "Proposed repository structure" is substantially stale

Lists `plugin/`, `migrations/`, `templates/`, a `src/investment_system/`
subpackage split into `validation/`, `indicators/`, `overlays/`, `scoring/`,
`costs/`, `benchmarks/`, `reporting/`, `storage/`, and
`docs/{methodology,data-dictionary,model-changelog,mistake-ledger,...}.md`.
None of this exists — the real layout is flat modules
(`indicators.py`, `costs.py`, `validation.py`, ...) plus `docs/wiki/*.md`. Not
wrong (it's explicitly labeled "Proposed"), but unlike most other sections it
has no pointer to `docs/wiki/architecture.md` for what's actually there,
so a reader has no signal how stale it's become.

### Verified correct (checked, not an issue)

- **7 September 2026 is genuinely a Monday** — confirmed directly
  (`datetime.date(2026, 9, 7).strftime('%A')` → `Monday`). This is repeated as
  a load-bearing fact in three places (header, "Frozen reports and model
  versioning", closing line) and the whole Monday-only gate depends on it
  being right.

## Codex's findings

### C1. Embedded report example is not schema-compatible

The conceptual JSON example in the design document differed from the
canonical repository schema:

- it used `"NO BUY"` rather than the schema's `"NO_BUY"`;
- sentiment examples omitted `status`, `provider`, `retrieved_at`, and
  explicit unavailable reasons;
- the BLAKE2b section was simplified compared with `blake2b_gate`;
- the current `operator_thesis` field was absent;
- several current validator-required fields were not represented.

The document says the repository schema is authoritative, but the example
could still mislead future implementation. Prefer a link to the canonical
schema with only a small explanatory excerpt, or update the example fully.
(Converges with Claude Code's finding #1 above.)

### C2. BTCB2 pending-verification behavior needed one explicit rule

At the time, the document recorded BTCB2 as included in Model v1.1 by
operator decision while the BLAKE2b checks remained important, but didn't
state plainly that BTCB2 could appear in the universe and receive technical
observations while still being barred from a BUY tier or positive
recommendation until the evidence fields passed. (Superseded: BTCB2 is no
longer in the universe; the current establishment-gate section states this
distinction explicitly for whenever it re-enters.)

### C3. BTCB2 lacked a dedicated asset overlay

The asset-specific overlay section listed IVV, NDQ, VAS, VGS, IZZ, VAE, Gold,
and Cash, but not BTCB2. Recommended overlay content: price-source
reliability, venue risk, liquidity and spread/slippage, custody and
withdrawal capability, chain/security verification, fork or implementation
risk, correlation with BTC, and invalidation conditions. (Now folded into
the establishment gate's own overlay requirement for whenever BTCB2 clears
it.)

### C4. Finnhub implementation scope wasn't reflected in the design

The design described market-data APIs at a broad level without distinguishing
implemented (Finnhub single quotes) from planned (historical candles, weekly
aggregation, adjusted ETF price history, fundamentals/macro, sentiment,
BTCB2/Neoxa market data) functionality. A single quote cannot produce the
required 20W/50W/200W indicators.

### C5. Repeated policy blocks

Monday-only/freeze rules, BTC BUY/SELL requirements, BLAKE2b rules, cash
hurdle behavior, secret handling, report/schema requirements, and MCP
fail-closed behavior were each repeated at length across the document.
(Converges with Claude Code's finding #4 above.) Recommended: one
authoritative section per topic with short cross-references elsewhere, while
keeping brief repetition of the safety-critical items (no automated trade
execution, no secrets in artifacts, fail closed on critical data problems,
separate BTC BUY/SELL, explicit confirmation before freezing) near execution
points.

### C6. Fedora operating model needed a clearer architecture split

Recommended stating explicitly that the Fedora home server runs scheduled
deterministic ingestion, SQLite snapshots, and report drafts, while the
Fedora desktop / interactive session handles qualitative review, explicit
freeze approval, and MCP interaction.

### C7. Open questions included resolved decisions

At the time, the "Current open questions" section still listed items already
resolved (model version, Wilder RSI, BTCB2 in universe, Fedora-only,
Discord-excluded). Recommended splitting into a dated "Decisions made"
section versus genuinely open questions. (Applied — see
`INVESTMENT_DECISION_SYSTEM.md`'s "Decisions already made" subsection, now
also recording the BTCB2 reversal and the single-agent development change.)

### C8. Target repository structure was partly historical

The proposed repository tree listed planned files that don't exist
(plugin, MCP server, templates, migrations, several docs). Acceptable as a
target architecture, but should be labelled clearly as planned rather than
read as a current inventory. (Converges with Claude Code's finding #6 above.)

## Where the two reviews converged

Both independently flagged: the embedded JSON example's schema incompatibility
(#1/C1), the BTCB2 hard-constraint overstatement (#2/C2), and the repeated
policy blocks (#4/C5). Each also caught things the other missed: Claude Code
empirically ran the doc's example through the real validator and verified the
"7 September 2026 is a Monday" claim directly; Codex caught the missing BTCB2
overlay section, the stale open-questions list, and the unstated Fedora
desktop/server split.

## Current conclusion

The document is suitable as a long-range design specification when read
alongside the repository schema, config, tests, and wiki — it is not a
substitute for those executable contracts. Findings #1/#3/#5/#6 and C1/C4/C8
are mechanical corrections (bring the doc's prose/examples in line with the
authoritative schema/code) and remain open at time of archiving. Findings
#2/#4 and C5/C6 involve wording judgment calls rather than pure mechanical
fixes. C2, C3, and C7 have since been addressed by the establishment-gate
rewrite and the "Decisions already made" section.
