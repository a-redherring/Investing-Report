# Changelog

Dated log of material changes to code behavior (not every commit — just things a
future reader would otherwise have to discover by diffing). Newest first.

## 2026-09-07 — FRED macro-indicator fetcher; fundamental valuation confirmed unautomatable for now

Follow-up to the `candidates.py` entry below: with scoring/ranking deferred
pending operator-decided weights/thresholds, the next honest question was
whether the two missing three-layer-model inputs (fundamental valuation,
regime) could be sourced at all. Researched before writing any code, since
forcing an automated classifier here on invented thresholds would repeat
the exact mistake scoring/ranking was just deferred to avoid.

**Fundamental valuation: no viable free source found.**

- No free, machine-readable ASX index valuation data exists. The RBA
  publishes ASX 200 dividend/P/E statistics, but only as PDF — no CSV/API.
  The real S&P/ASX 200 P/E is Refinitiv-sourced and not freely republished
  anywhere found.
- A promising free, keyless GitHub-hosted mirror of the Shiller S&P 500
  dataset (P/E10, dividend, earnings) was checked directly, not just
  assumed reliable from its listing page — its valuation columns
  (`Dividend`, `Earnings`, `PE10`) are zeroed out for every month since
  **2023-06** per the dataset's own notes (confirmed against real 2026 rows:
  only the raw index price is populated, valuation fields are all `0.0`).
  Using it for a "current valuation" reading would have silently violated
  this project's own fail-closed staleness rule.
- It would only have covered the US index anyway (IVV, loosely NDQ) — no
  help for VAS/IZZ/VAE, and gold/BTC have no P/E concept at all.
- Conclusion: this layer stays qualitative/interactive-AI judgment, per
  this document's own original architecture — not a gap left to close
  later, a deliberate fit with what the design already intended.

**Regime: partially automatable, but not as a mechanical formula.** FRED
(Federal Reserve Bank of St. Louis) is free, official, documented, and
covers what the regime inputs list needs — VIX, yield curve, credit
spreads, the fed funds rate — via an instant free-signup API key (same
tier as Alpha Vantage/CoinGecko's demo keys, confirmed via FRED's own
docs). But synthesizing those numbers into one of the seven regime labels
(`Deteriorating`/`Stable`/`Improving`/`Structural Bull`/`Structural
Breakout`/`Crisis`/`Unclear`) is a multi-factor judgment call, not a
threshold formula the way the technical layer's "stretch" label is —
hardcoding that mapping would mean inventing the same kind of thresholds
already declined for scoring. Confirmed with the operator before building:
fetch raw numbers only, classify nothing.

**New `ingestion.fred.fetch_series_latest()`** and
**`ingestion.data_sources.FredConfig`**. New CLI: `investment-system
fetch-macro <indicator>`, where `<indicator>` is a mnemonic (`vix`,
`yield_curve_10y2y`, `credit_spread_ig`, `credit_spread_hy`,
`fed_funds_rate`) mapped in `cli.py`'s `_MACRO_SERIES` to the real FRED
series ID.

**A real, documented deviation from this project's own design contract**:
every other adapter sends its API key as a header, "never the URL/query
string" — FRED's API only accepts the key as a URL parameter; there is no
header alternative. Handled by having `ingestion.fred`'s transport-error
paths never include the constructed request URL in any message (unlike
`ingestion.finnhub`/`yahoo`/`cnn_fear_greed`, where the URL contains no
secret and is safe to log) — the key is never in a log line, exception, or
the snapshot's own metadata, only in the one outbound request. Locked in
with a regression test (`test_api_key_never_appears_in_snapshot_or_error`)
that positively asserts the key *is* in the constructed URL (so the test
can't pass trivially) while confirming it never reaches the snapshot
content, snapshot metadata, or survives into any error path.

Also handles a real FRED-specific parsing quirk found in their own
documentation: a missing/not-yet-published observation is represented as
the literal string `"."`, not `null` or an omitted field.
`fetch_series_latest()` requests the 10 most recent observations and walks
forward past any `"."` entries to the latest real value, rather than
crashing on the next holiday/reporting lag or treating `"."` as zero.

Built entirely against FRED's own documented response shape and tested
offline with fixtures matching it exactly — no FRED API key was available
in this environment to verify live end-to-end, unlike every other adapter
this session (Finnhub, Alpha Vantage, Yahoo, CoinGecko were all verified
against the real network). The operator can optionally get a free key and
run `fetch-macro vix` for a final live check.

**13 new tests** (`tests/test_ingestion_fred.py` + 5 fixtures under
`tests/fixtures/fred/`). Full suite: 104 passed. No new dependency.

**What's still not built**: no regime classifier, no valuation source of
any kind, nothing calls `fetch-macro` automatically or feeds it into
`candidates.py`.

## 2026-09-07 — deterministic feature assembly (`candidates.py`); scoring/ranking deliberately deferred

Started roadmap item 4 ("Build deterministic feature assembly, scoring,
ranking, and draft-report generation"), but split it: feature assembly is
built; scoring/ranking is explicitly deferred pending operator decisions on
component weights and hard-gate/sizing-tier thresholds (open questions #8,
#9). Confirmed with the operator before writing any code — building a
scoring formula on invented numbers would be exactly the kind of silent
guess this project's fail-closed design exists to prevent.

**New `candidates.assemble_candidates()`**: one `Candidate` record per
`config/universe.yaml` asset (`symbol`, `currency`, `core`, `technical`,
`valuation`, `regime`, `confidence`, `hard_gates_passed`, `rationale`),
combining the real technical signal from `indicators.calculate()` (when
price data exists for that asset) with an honest placeholder for the two
required layers that have no data source at all yet — fundamental
valuation (`"Insufficient Data"`) and regime (`"Unclear"`). New CLI:
`investment-system candidates <csv>` (`signals`' sibling, printing per-asset
`Candidate` records instead of raw `TechnicalSnapshot`s).

**A real design decision, not just plumbing**: since valuation and regime
are structurally absent — not merely uncertain, but never computed by any
code in this repository — every candidate's `confidence` is forced to
`"insufficient"` and `hard_gates_passed` to `False`, regardless of how
complete the technical data is. This is the direct, honest consequence of
the design doc's own rule that missing critical data forces no trade,
applied to 2 of the 3 required layers being entirely unbuilt; it is not a
threshold anyone invented, and it flips automatically once valuation/regime
providers exist. Locked in with a regression test
(`test_confidence_and_hard_gates_are_insufficient_even_with_full_technical_history`)
using a synthetic 210-week series with complete 200-week-MA history, to
make sure a *complete* technical signal is never mistaken for a *complete*
analysis.

Every configured universe asset gets an entry regardless of whether the
given CSV has price data for it — a missing asset produces
`technical: null` and an explanatory rationale, not a silent omission.
Verified end-to-end against real fetched data: ran `fetch-history` for all
8 price-bearing assets, merged the output, and confirmed `candidates`
produces sane technical fields for each (real trend/stretch/drawdown) while
`CASH` (which never has a price series) correctly shows `technical: null`.

**3 new tests** (`tests/test_candidates.py`). Full suite: 91 passed. No new
dependency.

**What's still not built**: scoring (component weights), hard gates beyond
the data-sufficiency ones already forced above, sizing-tier thresholds,
ranking, and draft-report generation — all deferred to the same open
questions. `candidates.py` produces the *input* a future scoring step would
consume; it is not itself part of the frozen-report schema (the schema's
`rankings[]` shape has no `valuation`/`regime`/`technical` sub-fields —
those get distilled into `confidence` + `rationale` + `hard_gates_passed`
only once a real scoring step exists).

## 2026-09-07 — sentiment ingestion (Alternative.me crypto, CNN equity)

Roadmap item 3 ("Decide and document equity/crypto sentiment providers,
freshness rules, and unavailable-state behavior") — decided and built,
following the same empirical-verification discipline used for the
historical-candle providers.

- **Crypto Fear & Greed: Alternative.me's `/fng/` endpoint.** Official,
  documented, free, no key required — an easy, unambiguous choice; no other
  candidate was seriously considered since this is the de facto standard
  source for exactly this index.
- **Equity Fear & Greed: CNN's Fear & Greed Index**, via its unofficial
  chart-data endpoint (`production.dataviz.cnn.io/index/fearandgreed/graphdata`).
  No official free alternative was found. Confirmed empirically: an
  unauthenticated request returns the literal plain-text body `"I'm a
  teapot. You're a bot."`, not JSON and not an HTTP error status; adding a
  browser-like `User-Agent` and a `Referer` matching the real page
  (`cnn.com/markets/fear-and-greed`) is enough to pass. Same
  unofficial-endpoint risk profile already accepted for `ingestion.yahoo`
  (no ToS/SLA), stated plainly rather than silently assumed reliable.

**New `ingestion.sentiment.SentimentObservation`** (the shared contract both
adapters produce: `value`, `category`, `provider`, `effective_at`,
`retrieved_at`, `snapshot_id` — mirrors the report schema's
`sentimentObservation` shape closely enough to embed directly with
`status: "observed"` added at the point of use), **`ingestion.alternative_me.fetch_crypto_fear_greed()`**,
and **`ingestion.cnn_fear_greed.fetch_equity_fear_greed()`**. New CLI:
`investment-system fetch-sentiment equity|crypto` — same
deterministic-callable/CLI-boundary pattern as `fetch-quote`/`fetch-history`,
prints the observation or a structured error, exits 1 on any
`IngestionError`. Neither category string is case-normalized across
providers (Alternative.me sends Title Case, CNN sends lowercase) — passed
through as each provider states it, not silently rewritten.

Both fail closed on a reading older than a configured `max_age_seconds`:
2 days for crypto (24/7 markets, updates daily without exception), 4 days
for equities (accounts for a normal Friday-to-Monday weekend gap when
equity markets are closed and CNN's index doesn't update).

**Verified end-to-end against the real network**, not just fixtures: both
`fetch-sentiment crypto` and `fetch-sentiment equity` return real, current
readings (71/"Greed" and 41.86/"fear" respectively, as of this writing).

**14 new tests** (`tests/test_ingestion_alternative_me.py`,
`tests/test_ingestion_cnn_fear_greed.py` + fixtures under
`tests/fixtures/alternative_me/`, `tests/fixtures/cnn_fear_greed/`),
including a regression test locking in the exact real "teapot" bot-block
response so it's never mistaken for a crash. Full suite: 88 passed. No new
dependency — stdlib `urllib`, matching every other adapter.

**What's still not built**: no report-generation step calls either adapter
yet or assembles a report's `sentiment` section; no rule exists yet for how
a sentiment reading actually modifies a ranking/BTC decision (still an open
question in `INVESTMENT_DECISION_SYSTEM.md`); neither adapter is wired into
any systemd unit.

## 2026-09-07 — Neoxa references removed from live documentation

Operator direction: remove Neoxa Exchange from the project entirely.
Scrubbed every mention from currently-maintained documentation —
`INVESTMENT_DECISION_SYSTEM.md` (the candidate-tracking table row, and the
two crypto-asset-inclusion-gate criteria that used "Neoxa" as an illustrative
example of a single venue/exchange-only custody), `docs/candidates/BTCB2.md`
(same pattern, plus its custody/independent-verifiability evidence entries),
`docs/wiki/configuration.md`, `docs/wiki/ingestion.md`, `docs/wiki/roadmap.md`,
`docs/wiki/reports.md`, `README.md`, and `FULL_PROGRAM_DESCRIPTION.md`.

None of the gate criteria themselves actually depended on naming Neoxa
specifically — "Neoxa" appeared only as an illustrative example within
already-generic rules ("a single venue never satisfies this," "exchange-only
custody does not satisfy this"), so removing the name changes no
requirement or pass/fail status. BTCB2's candidate-tracking table entry, which
did assert a specific fact ("BTCB2/USDC reference pair on Neoxa Exchange"),
now reads "no independently verified multi-venue listing established" —
criteria 2 (liquidity) and 3 (price discovery) were already `TODO`/unsourced
in `docs/candidates/BTCB2.md`, so this is a more accurate statement of the
same unchanged status, not a new claim.

**BTCB2's candidate tracking itself is untouched** — this was a request to
remove Neoxa specifically, not to end BTCB2's candidacy; the crypto asset
inclusion gate and its six criteria are unaffected.

**Deliberately left unedited**, per this project's own established practice
of not rewriting historical record: `docs/archive/` (frozen point-in-time
build history) and every existing dated entry below in this changelog
(each remains an accurate record of what was true when it was written,
including the 2026-09-04 entries describing BTCB2's now-reverted
Neoxa-listed v1.1 inclusion). No code, schema, or config change — this was
documentation only. Full suite: 74 passed, unchanged.

## 2026-09-07 — gold vehicle decided (ASX:GOLD); historical ingestion now covers all 8 price-bearing assets

Resolved `INVESTMENT_DECISION_SYSTEM.md`'s open question #5 ("How should
gold be implemented: spot reference, ASX ETF, or another vehicle, and in
which currency?") — an explicit operator decision, following the same
"verify before relying on it" discipline used for the ASX-equity/BTC
provider selection above, not a silent inference from the placeholder
`GOLD` symbol already in `config/universe.yaml`.

**Compared four ASX-listed gold ETFs on both data quality and economic
exposure before deciding:**

- **GOLD.AX** (Global X Physical Gold, unhedged) — one isolated bad tick at
  the same 2010-2011 boundary IVV's corruption occupies, clean otherwise
  (819 clean bars, ~15.8 years, after it). **Chosen**: largest/most liquid
  ASX gold ETF, and the symbol already sitting in `config/universe.yaml`
  turned out to already name this exact real, currently-traded instrument.
- **QAU.AX** (BetaShares, currency-hedged into AUD) — completely clean Yahoo
  data, zero anomalies. Considered and passed over: hedging removes the
  AUD/USD diversification benefit unhedged gold provides for an
  AUD-denominated investor, at a higher management fee (0.59% vs 0.40%).
- **PMGOLD.AX** (Perth Mint Gold, unhedged) — ruled out on data reliability:
  Yahoo's own metadata shows `fiftyTwoWeekHigh: $78.99` against
  `regularMarketPrice: $17.94`, a >4x disparity with no stock split
  recorded anywhere to explain it, plus intermittent monthly-spaced gaps in
  the weekly series as recently as 2020.
- **NUGG.AX** (VanEck) — clean data but only 197 weekly bars since its
  December 2022 listing (~3.8 years) — too little history for a 200-week
  moving average regardless of data quality.

**`GOLD.AX` added to `cli.py`'s `_HISTORY_PROVIDERS`**, pinned to
`range="15y"` (784 clean bars, confirmed zero anomalies via the same
implausible-jump scan used for every other ticker) — the same treatment
IVV's isolated corrupted window already received. No new adapter code was
needed: `ingestion.yahoo.fetch_weekly_history()` already handles any Yahoo
symbol generically. Verified end-to-end: `fetch-history GOLD` followed by
`investment-system signals` produces a plausible `-17.8%` drawdown from a
real all-time high, not a corrupted or implausible figure.

Updated `INVESTMENT_DECISION_SYSTEM.md` (tracked-universe table, the Gold
asset-overlay section, "Decisions already made", and struck through open
question #5 with its resolution — matching the document's own established
convention for resolved questions, e.g. the crypto-inclusion-gate item),
`docs/wiki/ingestion.md` (the comparison table above), and
`docs/wiki/configuration.md`. Every universe asset except CASH (which has no
price series to fetch) is now sourced. Full suite: 74 passed, unchanged —
this needed no new adapter tests since `GOLD.AX` runs through the
already-tested `fetch_weekly_history()` generically.

## 2026-09-07 — historical weekly-candle ingestion (Yahoo Finance)

Roadmap item 1 ("Add provider historical-candle ingestion and a canonical
weekly-price contract") was explicitly gated on "verify the chosen
provider's actual tier/access before relying on it" — this entry is that
verification, done empirically before writing any adapter code, plus the
adapter itself and two real data-quality bugs found and fixed along the way.

**Provider selection (tested against a real key, not just public reports):**

- **Finnhub free tier** (the operator's actual plan): confirmed blocked for
  historical candles — `/stock/candle` returns `403` for both a US symbol
  (AAPL) and an ASX symbol (IVV.AX), and `/crypto/candle` is blocked too
  (BTC). The plain `/quote` endpoint still works.
- **Alpha Vantage free tier**: `SYMBOL_SEARCH` for IVV/VAS returned zero
  Australia-region matches (only US/Frankfurt/Brazil/India), and direct
  `TIME_SERIES_WEEKLY_ADJUSTED` calls with an `ASX:` prefix returned empty
  objects — no real ASX coverage despite older community reports otherwise.
- **Twelve Data free tier**: explicitly US-equities-only per their own
  pricing page.
- **Stooq**: right shape (free CSV, daily/weekly/monthly, no key) but now
  gated by a client-side JS proof-of-work bot challenge — confirmed via a
  direct request returning a `/__verify` SHA-256 puzzle page instead of data.
  Not automatable headlessly.
- **CoinGecko**: solid for BTC daily prices with no key, but the public/free
  tier hard-caps historical range at 365 trailing days (`error_code 10012`,
  confirmed to apply to both keyless and free-Demo-key tiers) — not enough
  for a 200-week MA. **Built, then removed** once Yahoo was confirmed to
  cover BTC-USD with the same long, gap-free weekly history as the ASX
  ETFs — keeping a second provider with no capability advantage over the
  first would have been pure redundancy.
- **Yahoo Finance's chart endpoint** (unofficial/undocumented, no ToS/SLA):
  the only source that returned real multi-year weekly OHLC for ASX-listed
  ETFs, free, unauthenticated. Used for both the ASX equities and BTC.

**New `ingestion.yahoo.fetch_weekly_history()`** and
**`ingestion.candles.WeeklyBar`** (the shared weekly-bar contract). New CLI:
`investment-system fetch-history <asset> [--range WINDOW] [--output-dir DIR]`
— writes `data/history/<ASSET>.csv` in the exact `asset,date,close` shape
`engine.load_prices()` already reads, so it feeds `investment-system signals`
with no other code change. Covers IVV, NDQ, VAS, VGS, IZZ, VAE (via
`<SYMBOL>.AX`) and BTC (via `BTC-USD`). **GOLD is deliberately unsupported**
— its vehicle (spot, an ASX ETF, or something else) is still an open design
question independent of any provider's API; guessing a ticker would have
silently pre-empted that decision. CASH has no price series to fetch.

**Two real data-quality bugs found and fixed empirically, not guessed at:**

1. **`range="max"` silently coarsens to monthly bars.** Requesting
   `interval=1wk&range=max` for a long-lived symbol returns bars with
   ~28-31 day deltas, not ~7 — with no error, warning, or signal of the
   downgrade anywhere in the response. Every other explicit range tested, up
   to `"20y"`, returns genuine gap-free weekly bars. `fetch_weekly_history()`
   therefore defaults to `"20y"`, never `"max"`.
2. **Yahoo's `"IVV.AX"` history is corrupted from 2010 to 2017** — real
   values (~$120+) repeatedly flip-flop against bogus ones (~$8-17) roughly
   15x, with no stock split recorded to explain it (checked directly against
   `events=splits`, and against both raw `close` and dividend/split-adjusted
   `adjclose`, which show the identical bogus values). Scanned all 7 tickers
   for the same anomaly: VAS, VGS, NDQ, IZZ, VAE are completely clean across
   their full history; BTC-USD's one large single-week move (~-33.5% around
   2020-03-02) is the real, well-documented COVID crash, not corrupted data.
   Added a permanent sanity check to `_parse_weekly_history()`: any
   single-week close-to-close move beyond a 5x/0.2x bound is rejected
   outright (comfortably wider than genuine extreme volatility, so it never
   flags a real crash) — this protects any future ticker against the same
   class of corruption, not just a one-off workaround for IVV. IVV's default
   fetch range is pinned to `"10y"` (the shortest range confirmed clean,
   still ~10x the 200-week MA minimum) in `cli.py`'s per-asset provider
   table; every other asset defaults to `"20y"`. A `--range` CLI override
   exists for if a similar issue is ever found elsewhere.

**Verified end-to-end against the real network**, not just fixtures: fetched
real weekly history for all 7 supported assets, fed the combined CSV straight
into `investment-system signals`, and confirmed every indicator looks
sane — in particular IVV's `drawdown_from_ath_pct` went from an implausible
-78% (before the sanity check existed, reading straight into 2010-era
corrupted data) to a plausible -2.9% after the fix.

**8 new tests** (`tests/test_ingestion_yahoo.py` + 4 fixtures under
`tests/fixtures/yahoo/`), including a regression test locking in the
corrupted-data rejection and a companion test confirming a real extreme
crash is *not* rejected. Full suite: 74 passed. No new dependency — stdlib
`urllib`, matching `ingestion.finnhub`.

**What's still not built**: nothing calls `fetch-history` automatically (no
cron/systemd/CLI-chain); nothing feeds its output into a scoring/ranking
step (none exists yet — see the rest of this roadmap); gold ingestion,
pending the vehicle decision above.

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
