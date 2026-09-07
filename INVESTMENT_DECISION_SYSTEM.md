# Monday Investment Decision System

> **Status:** Design specification  
> **Planned first live report:** **Report #001 — Monday, 7 September 2026**  
> **Current model:** **Model v1.0**
> **Practice reports:** `P-001`, `P-002`, and every other `P-*` report are rehearsals only. They are not live recommendations, trades, or part of the permanent performance record.

## Disclaimer

This repository documents a personal decision process for research and education. It is not personal financial advice, a promise of performance, or an instruction to trade. Tax, suitability, liquidity, product, custody, and regulatory considerations require independent review. All fees, yields, market data, product details, and broker terms must be re-verified at decision time.

No API key, token, credential, account identifier, or other secret belongs in reports, logs, fixtures, commits, screenshots, or issues.

## Purpose

The system produces one disciplined, auditable investment decision each Monday from a deliberately small universe. It is intended to answer five questions:

1. What are the three best uses of new money this week?
2. Does any risk asset clear the hurdle set by cash yielding an assumed 5%?
3. If an asset wins, is the evidence strong enough for A$999, A$2,000, or A$4,000?
4. Should any existing position be held, reduced, or sold?
5. Was the decision process consistent, reproducible, and honest about uncertainty?

The system is a decision aid, not an automatic trading bot. Deterministic calculations create the factual base; qualitative analysis explains context and uncertainty; the final Monday report freezes exactly what was known and decided at the time.

## Document authority and maintenance

This specification explains intent and policy; it is not a second implementation
of every data structure. The repository is authoritative for executable detail:

- `config/*.yaml` is authoritative for the current universe and model parameters;
- `schemas/frozen-report.schema.json` is authoritative for report structure;
- the Python validator and tests are authoritative for executable validation;
- `docs/wiki/` records the behavior that is actually implemented.

The report field map and Markdown example later in this document are explanatory
only. When they differ from the repository schema, the repository schema wins
and this document must be corrected in the same change. The Monday checklist and
MCP enforcement rules are derived operational views of the same underlying
freeze gate, not separate decision systems.

## Philosophy

The governing idea is:

> **Participate in long-term compounding, but preserve meaningful capital for genuine opportunities and dislocations.**

Key principles:

- Do not equate a good asset with a good entry price.
- Do not equate an expensive core holding with an automatic sell.
- Do not wait indefinitely for perfect value when the opportunity cost of missing long-term compounding is high.
- Do not buy merely because an asset has fallen; distinguish cheapness from a deteriorating thesis.
- Do not chase a powerful trend merely because price is rising.
- Treat cash as an investable alternative with a real hurdle rate and option value.
- Separate observable facts, deterministic calculations, model classifications, qualitative judgments, and final decisions.
- Prefer one understandable decision over false precision.
- Preserve the record. Never rewrite an old live report using information learned later.

## Tracked universe

| Asset | Implementation / reference | Role | Core holding? | Principal question |
|---|---|---|---:|---|
| IVV | ASX-listed IVV | US large-cap equities | Yes | Is long-term compounding worth buying despite valuation and cycle risk? |
| NDQ | ASX-listed NDQ | Nasdaq-100 growth tilt | No | Is growth attractive enough after accounting for valuation and rate sensitivity? |
| VAS | ASX-listed VAS | Australian equities | Yes | Is the domestic market attractive versus cash and global alternatives? |
| VGS | ASX-listed VGS | Developed global equities | Yes | Does broad developed-market diversification merit accumulation? |
| IZZ | ASX-listed IZZ | China large-cap exposure | No | Does low valuation outweigh structural, policy, and trend risks? |
| VAE | ASX-listed VAE | Asian equities excluding Japan | Yes | Does diversified Asian growth offer better risk-adjusted value than concentrated China exposure? |
| Gold | ASX:GOLD (Global X Physical Gold, unhedged) | Diversifier / real asset | No | Is the macro regime supportive enough to justify the opportunity cost of a non-yielding asset? |
| BTC | Bitcoin | High-volatility cyclical asset | No | Do cycle, sentiment, valuation proxies, and trend justify buying or selling? |
| Cash | AUD cash at an assumed 5% p.a. | Reserve and benchmark | N/A | Is waiting the highest-quality use of capital? |

The universe is closed by default. Adding any asset requires an explicit model-version change, data specification, fee model, asset-specific overlay, and benchmark treatment. A cryptocurrency candidate must additionally clear the [crypto asset inclusion gate](#crypto-asset-inclusion-gate) before a model-version change may propose adding it — there is no separate blanket ban on non-BTC crypto, but in practice BTCB2 is currently the only candidate under consideration.

### Candidate assets not yet in the universe

| Candidate | Reference | Status | Gate | Tracking |
|---|---|---|---|---|
| BTCB2 | No independently verified multi-venue listing established (see criteria 2/3 below) | Tracked as a candidate only; **not in `config/universe.yaml`**, not ranked, not reported on | Must clear the crypto asset inclusion gate below before any model-version change adds it | [`docs/candidates/BTCB2.md`](docs/candidates/BTCB2.md) |

Tracking a candidate here is not an endorsement, not a partial inclusion, and not a signal. It exists so the gate has something concrete to be checked against on a recurring basis, not so the asset accrues implicit legitimacy by being named in this document.

### Core holdings and Waiting Risk

IVV, VAS, VGS, and VAE are core long-term accumulation holdings. They receive a separate **Waiting Risk** assessment:

- **Low:** waiting is unlikely to cause material opportunity cost, or the regime is hostile.
- **Medium:** the cost of delay and the benefit of patience are balanced.
- **High:** the asset is a credible long-term compounder in a healthy regime and remaining entirely in cash risks missing meaningful compounding.

Waiting Risk prevents “expensive” from becoming a permanent veto. A core ETF can qualify for an A$999 accumulation buy while moderately expensive if its earnings, trend, diversification role, and regime remain healthy. Waiting Risk does not justify A$2,000 or A$4,000 by itself.

BTC, gold, NDQ, and IZZ do not inherit the core baseline-accumulation privilege. They must clear their own higher, asset-specific hurdle.

## Operating cadence: Monday only

- Reports may be prepared or rehearsed on other days, but live execution decisions are made **only on Monday**.
- Friday's completed weekly close is the primary technical cutoff. Weekend information may update the regime or risk assessment before the Monday report is frozen.
- A non-Monday report must be labelled `Practice Report P-###` or `Preview` and must state that it is non-live.
- The live report ranks the entire universe but ordinarily selects at most one new-money action.
- If no asset clears the cash hurdle, the correct decision is **A$0 invested**.
- Emergency risk management outside Monday is not yet authorised by this specification; if later introduced, it must use explicit, narrow rules and a new model version.

## Fee-aware sizing

The sizing ladder expresses the strength and type of opportunity, not just confidence:

| Decision | Meaning | Typical use |
|---:|---|---|
| **A$0** | Cash wins | No candidate offers sufficient expected reward for its risk and costs |
| **A$999** | Accumulation capital | Maintain participation in a core compounder, or take a modest starter position |
| **A$2,000** | Opportunity capital | Genuinely attractive valuation/setup with adequate confirmation |
| **A$4,000** | Dislocation capital | Rare, exceptional setup: major mispricing or capitulation with thesis intact and deterioration stabilising |

For CMC Invest Australia, the working assumption is that a qualifying first ASX buy under A$1,000 per security per day may receive A$0 brokerage, while other standard ASX buys and sells may be charged the greater of A$11 or 0.10%. **These terms are not hard-coded facts:** the live report must verify the current broker rules before relying on them.

Under that working schedule, indicative brokerage drag is:

| ASX parcel | Indicative brokerage | Indicative drag |
|---:|---:|---:|
| A$999 qualifying buy | A$0 | 0.000% |
| A$2,000 buy | A$11 | 0.550% |
| A$4,000 buy | A$11 | 0.275% |

“Brokerage free” never means economically free. Every recommendation must consider:

- bid/ask spread and market impact;
- AUD/USD or other FX conversion costs and currency exposure;
- ETF management fees and tracking difference;
- crypto exchange, network, custody, and withdrawal costs;
- tax consequences where relevant;
- product liquidity and execution quality;
- the cost of selling, not only buying.

BTC is sized in approximately A$1,000/A$2,000/A$4,000 equivalents after its own venue costs; it does not receive the ASX A$999 brokerage treatment.

## The three-layer model

Each risk asset is evaluated on three separate layers. They must not be collapsed into one vague label.

### 1. Fundamental / macro valuation

Question: **What is the asset plausibly worth, and what return is available relative to alternatives?**

Possible labels: `Very Cheap`, `Cheap`, `Fair`, `Expensive`, `Very Expensive`, or `Insufficient Data`.

Inputs vary by asset and may include earnings yield, forward and trailing multiples, cyclically adjusted measures, dividend yield, earnings growth, real yields, credit conditions, inflation, currency, liquidity, fiscal conditions, supply/demand, adoption, and valuation relative to history and peers.

Valuation is not inferred solely from distance to a moving average. Price can be technically extended while fundamental value improves, or technically depressed while the underlying regime deteriorates.

### 2. Technical stretch and trend

Question: **Where is price relative to its recent, intermediate, and long-term structure?**

Required weekly indicators:

- 20-week simple moving average (`20W MA`);
- 50-week simple moving average (`50W MA`);
- 200-week simple moving average (`200W MA`);
- weekly RSI, with the period recorded;
- weekly MACD, including line, signal, histogram, and parameters;
- percentage distance from each moving average;
- percentage drawdown from the all-time high (`ATH`);
- slope/direction of the 50W and 200W averages;
- relevant completed-week breakout, breakdown, support, and resistance states.

Example calculations:

```text
distance_from_ma_pct = (weekly_close / moving_average - 1) * 100
drawdown_from_ath_pct = (weekly_close / historical_ath - 1) * 100
```

Possible stretch labels: `Deeply Oversold`, `Oversold`, `Normal`, `Extended`, `Extremely Extended`, or `Insufficient Data`.

Possible trend labels: `Strong Downtrend`, `Downtrend`, `Mixed`, `Uptrend`, `Strong Uptrend`, or `Insufficient Data`.

Indicator calculations must use a documented price basis: adjusted prices where distributions/splits require it, consistent weekly boundaries, and enough history for the indicator. A missing 200W history must be reported as missing, never approximated without disclosure. The exact implemented indicator contract is maintained in the repository's code/wiki; this section defines the requirement, not a second implementation.

### 3. Regime

Question: **Is the environment deteriorating, stable, improving, or undergoing a structural change?**

Possible labels: `Deteriorating`, `Stable`, `Improving`, `Structural Bull`, `Structural Breakout`, `Crisis`, or `Unclear`.

The regime layer combines measurable conditions that are not captured by valuation or price stretch: earnings direction, monetary and fiscal policy, rates and liquidity, recession/credit risk, market breadth, volatility, regulation, geopolitics, adoption, and asset-specific structural forces.

Regime claims require dated evidence and should state what would falsify them.

## Sentiment

The report includes two distinct sentiment series:

- **Equity Fear & Greed** for equity-market risk appetite.
- **Crypto Fear & Greed** for Bitcoin and crypto-specific risk appetite.

Each observation records provider, value, category, retrieval time, and effective date. The report schema is the canonical field contract; sentiment is a modifier, not a standalone trigger:

- `Extreme Fear` can strengthen a contrarian opportunity only if valuation and thesis quality are adequate and deterioration is stabilising.
- `Greed` or `Extreme Greed` can limit sizing, especially when price is extended.
- In a presumed BTC bear phase, a sharp rally plus Greed near resistance may strengthen a sell assessment rather than a buy assessment.

## Asset-specific overlays

### IVV

- S&P 500 earnings growth, revisions, margins, and breadth.
- Forward valuation and equity-risk compensation versus cash/bonds.
- US rates, inflation, liquidity, and recession risk.
- High Waiting Risk is possible in a healthy bull regime even when valuation is expensive.
- Midterm-cycle seasonality modifies patience and sizing but never acts as a deterministic sell rule.

### NDQ

- Growth-duration sensitivity to real and nominal yields.
- Concentration and mega-cap leadership.
- Technology/AI earnings durability, revisions, and capex economics.
- A correction is attractive only if the earnings thesis remains intact.

### VAS

- Australian valuation, earnings, dividends, and sector concentration.
- RBA policy, domestic inflation, housing/credit, AUD, commodities, and China exposure.
- Resource and financial-sector cycles require explicit treatment.

### VGS

- Developed-market valuation and earnings breadth.
- Geographic and currency composition.
- Overlap with IVV and the marginal diversification gained by buying VGS.

### IZZ

- Chinese/Hong Kong large-cap valuation rather than generic “China” headlines.
- Property, credit, consumption, deflation, regulation, policy support, geopolitics, and accessibility.
- Cheapness alone does not override a deteriorating regime or weak trend.

### VAE

- Country and sector composition across Asia excluding Japan.
- China exposure is assessed within a diversified regional portfolio.
- Asian growth, currencies, trade, policy, and geopolitical risks.
- Core status reflects its diversification role, but its Waiting Risk may be lower than IVV/VGS when the regional regime is uncertain.

### Gold

- Vehicle: **ASX:GOLD** (Global X Physical Gold, unhedged, AUD) — the largest
  and most liquid ASX-listed gold ETF, chosen over QAU (currency-hedged, no
  AUD-weakness diversification benefit, higher fee) and PMGOLD/NUGG (ruled
  out on data reliability/history depth — see
  [`docs/wiki/ingestion.md`](docs/wiki/ingestion.md)).
- Being unhedged, AUD-denominated returns reflect both the USD gold price
  *and* AUD/USD movements — this is the diversification property against AUD
  weakness the unhedged choice is for, not a defect to correct for.
- Real yields, nominal yields, USD, inflation expectations, fiscal credibility, central-bank demand, geopolitics, and investor flows.
- Distance above the 200W MA is technical stretch, not proof of fundamental overvaluation.
- In a structural bull regime, extension may justify “hold/don't chase” rather than “sell.”

### Cash

- The system assumes a 5% annual yield for comparison until replaced by a verified, after-fee rate.
- Cash has low nominal volatility and valuable optionality, but inflation, tax, reinvestment risk, and foregone asset growth matter.
- Cash can rank #1 and produces the explicit action `A$0 invested`.

## US midterm-cycle seasonality

US midterm-election seasonality is a contextual overlay for IVV, NDQ, and indirectly VGS. The working hypothesis is that uncertainty and drawdown risk can be elevated around the midterm period, potentially creating better entries.

Rules:

- Treat this as probabilistic seasonality, not prophecy.
- Do not sell or prohibit A$999 core accumulation solely because it is a midterm year.
- Preserve A$2,000/A$4,000 capital when valuations are elevated and the larger opportunity may improve.
- Record the exact historical definition and test window once the backtest is implemented.
- Measure whether the overlay adds value after costs; remove or reduce it if it does not.

## Bitcoin framework

### Four-year-cycle prior

The working prior is that Bitcoin follows a roughly four-year cycle and is currently in a **bear-market phase**. This is a hypothesis, not an immutable law.

Consequences of the prior:

- A 20–30% drawdown from ATH is not automatically cheap by BTC standards.
- A sharp rally can be a countertrend bear-market rally.
- Rally + Greed + approach to the 50W area can argue for patience or partial profit-taking.
- A more compelling buy combines a deep ATH drawdown, Fear/Extreme Fear, proximity to long-term support/200W, seller exhaustion, and stabilisation.
- Merely touching or falling below the 200W does not automatically justify A$4,000.
- Evidence that the cycle prior has failed must be described explicitly and can change the assessment.

### Mandatory BTC assessment (BTCB2 excluded pending its gate)

Every Monday report contains independent BTC BUY and SELL conclusions. BTCB2
is not currently in the universe and is not ranked, sized, or reported on as
an asset — see [Crypto asset inclusion gate](#crypto-asset-inclusion-gate)
for the gate it must clear first and [Bitcoin BLAKE2b monitoring](#bitcoin-blake2b-monitoring)
for the recurring monitoring that happens in the meantime. BTC and BTCB2 must
never be substituted for one another if and when BTCB2 is eventually added.

#### BTC BUY

Allowed report states are `BUY`, `WATCH`, `NO_BUY`, or `INSUFFICIENT_DATA`;
the dollar sizing tier is recorded separately in the ranking/action fields.

The assessment must cover cycle phase, drawdown from ATH, 20W/50W/200W position, weekly RSI/MACD, crypto sentiment, liquidity/regime, thesis risks, and venue costs.

#### BTC SELL

Allowed report states are `HOLD`, `CONSIDER_PARTIAL_SELL`, `PARTIAL_SELL`,
`EXIT`, or `INSUFFICIENT_DATA`, with any percentage sizing stated separately
and justified.

The assessment uses the existing-position reference basis of **US$60,000**. It must show the approximate unrealised percentage result from that basis while making clear that cost basis is context, not intrinsic value and not a reason to avoid a rational sale.

```text
gain_from_reference_pct = (btc_price_usd / 60000 - 1) * 100
```

A partial sell should require a confluence such as failed weekly resistance, loss of the 50W after a bear-market rally, deteriorating weekly momentum, Greed, weakening liquidity, or thesis impairment. Tax and execution consequences must be noted before an order is placed.

### Bitcoin BLAKE2b monitoring

The Monday process separately monitors the proposed Bitcoin proof-of-work change/fork from SHA256d to **BLAKE2b**. It is not treated as ordinary BTC price analysis. This monitoring is unconditional — it runs every report regardless of whether BTCB2 or any other BLAKE2b-related asset is in the universe.

### Crypto asset inclusion gate

There is no blanket ban on cryptocurrencies other than BTC; the universe is
closed by default (see above), and a crypto candidate faces the same
model-version-change process as any other asset, plus this additional gate.
In practice, BTCB2 is currently the only candidate under consideration, and
this section is written with it in mind, but the gate applies to any future
crypto candidate on the same terms.

BTCB2 is tracked only as a named candidate (see "Candidate assets not yet in
the universe" above) and is not in `config/universe.yaml`, not ranked, and
not sized. A prior model version (v1.1) added BTCB2 to the universe on
operator authorization; that inclusion was withdrawn and the model reverted
to v1.0 pending the asset actually clearing the gate below on its own
evidence, not on conviction.

#### Establishment gate

A cryptocurrency candidate (BTCB2 or any future candidate) becomes
eligible for a **new model-version change proposing its addition** to the
universe only when every one of the following is independently verified and
recorded, with sources, in at least four consecutive Monday reports (live or
practice) with no regression in between:

1. **Operational maturity.** Mainnet has run continuously for at least 3
   months, with no unresolved consensus-halting incident (chain split,
   rollback, or extended outage) during that period.
2. **Liquidity.** Trailing-30-day average daily trading volume of at least
   US$250,000, aggregated across **at least two independent, non-affiliated
   exchanges**. Volume on a single venue never satisfies this on its own.
3. **Price discovery.** At least two independent venues publish the
   reference pair, and the sampled price divergence between them is under 5%
   at report time.
4. **Custody.** A self-custody path exists via open-source wallet software,
   or a recognized third-party custodian/hardware-wallet vendor supports the
   asset. Exchange-only custody does not satisfy this.
5. **Independent verifiability.** A public block explorer and node software
   exist independent of any single exchange, so chain state can be verified
   without trusting one venue's word for it.
6. **Defined thesis and risk model.** A written, dated investment thesis and
   explicit invalidation conditions exist, addressing plausibility and risk
   modelling against the vulnerabilities the candidate responds to.

**Tracking.** No report-generation step exists yet to record progress
against these six criteria (see the roadmap), so
[`docs/candidates/BTCB2.md`](docs/candidates/BTCB2.md) is, for now, the one
place a candidate's status against each criterion — including the written
thesis and invalidation conditions criterion 6 requires — is recorded. A
status recorded only there is not yet independently verified in a Monday
report; it becomes load-bearing only once reproduced with sources across the
four consecutive reports this gate requires.

These thresholds are a working default, not a claim of precision — the
operator sets and may revise this list, including tightening, loosening, or
removing a criterion (a prior draft of this gate had a seventh criterion,
an independent security/code audit requirement, removed by operator
decision on 2026-09-06 as impractical for this asset), via an explicit
model-version change, the same way any other model parameter changes. Until
all six hold, BTCB2 receives monitoring only: each report records either a
material, sourced development or the fixed line `No sufficiently credible
BLAKE2b development changes the portfolio decision this week.` This gate is
not an endorsement of any asset, and tracking a candidate's progress toward
it is not itself a recommendation.

Once eligible, BTCB2 (or any future crypto candidate) still must not receive
an automatic BUY tier merely from clearing the gate — it enters the universe
subject to its own dedicated venue/liquidity/security/custody overlay and the
full three-layer model, on equal footing with every other asset, with no
grandfathered confidence or sizing advantage from having once been
provisionally configured under v1.1.

## Ranking and decision rules

Every live report ranks all eligible candidates and highlights:

1. **#1 — preferred use of new money**;
2. **#2 — best alternative**;
3. **#3 — next-best alternative**.

Cash is always eligible for all three ranks. Rank #1 may therefore be cash, producing A$0 investment.

The ranking must distinguish:

- attractiveness for new money;
- action on an existing holding;
- confidence in the data and thesis;
- Waiting Risk for core assets;
- sizing tier if selected.

Only #1 ordinarily receives new money. Exceptions require an explicit diversification or risk-control rule and a model-version change.

## Cash hurdle

A risk asset must offer a sufficiently attractive prospective return and portfolio role to compensate for:

- the assumed 5% cash yield;
- volatility and drawdown risk;
- uncertainty in valuation and regime;
- fees, spreads, FX, tax, and implementation friction;
- loss of optionality.

The comparison is not “cash yield versus equity earnings yield” alone. Equities can grow earnings and dividends; cash can be repriced downward and does not provide the same long-term growth exposure. Core Waiting Risk therefore modifies the hurdle for A$999 accumulation, but larger allocations need stronger evidence.

## Scoring-system concept

The engine may calculate a transparent score to enforce consistency, but **weights and thresholds are not finalised**. Model v1.0 should retain both component values and the human-readable reasoning rather than hide judgment behind a single number.

Candidate components include:

```text
provisional_score =
    valuation_component
  + technical_component
  + regime_component
  + sentiment_component
  + waiting_risk_component
  + asset_overlay_component
  - cash_hurdle_penalty
  - cost_and_liquidity_penalty
  - uncertainty_penalty
  - concentration_penalty
```

Design constraints:

- Component scales, directions, caps, interactions, and missing-data treatment must be explicit.
- Asset-specific overlays may adjust a score but cannot silently override failed hard gates.
- Strong trend must not double-count regime; Fear must not double-count drawdown; fees must not be ignored after ranking.
- A score maps to a candidate tier, but the final tier remains constrained by hard rules such as thesis integrity and data quality.
- Changing weights, thresholds, indicator definitions, or universe membership requires a new model version.
- Historical calibration must avoid look-ahead bias, survivorship bias, and repeated tuning to the same sample.

## Confidence and quality control

### Confidence labels

- **High:** primary/credible data are current, calculations are complete, sources agree, and the decision is robust to reasonable assumptions.
- **Medium:** the core evidence is adequate but one or more important uncertainties remain.
- **Low:** missing/stale data, source disagreement, unstable assumptions, or a highly uncertain regime could change the ranking.
- **Insufficient:** the system cannot responsibly classify or size the asset.

Low confidence cannot support A$4,000. An A$2,000 decision normally requires at least Medium confidence. Missing critical price, fee, liquidity, or thesis data forces `NO TRADE` for that asset.

### Mandatory checks before freezing a live report

- Timestamp and timezone are recorded (`Australia/Sydney`).
- Weekly price bars are complete and use the documented adjustment method.
- 20W/50W/200W, RSI, MACD, ATH, and distances are recomputed, not copied from prose.
- Split/distribution anomalies and stale quotes are checked.
- Market-data source and retrieval time are stored.
- Equity and crypto sentiment dates/providers are stored.
- Broker fees and cash yield assumptions are current or clearly labelled unverified.
- Currency units are explicit: `A$`/`AUD` versus `US$`/`USD`.
- BTC BUY and BTC SELL are both present.
- BLAKE2b monitoring is present.
- Every material qualitative claim has a dated source or is labelled as an assumption.
- The selected order is checked against available capital, existing concentration, liquidity, and costs.
- Contradictory indicators are reported rather than averaged away.
- No credential or secret appears anywhere in the frozen artifact.
- A deterministic hash is recorded for the frozen structured report where practical.

## Frozen reports and model versioning

The first intended live Monday report is **Report #001 on 7 September 2026 using Model v1.0**. The actual report is created only with information available at its freeze time. The repository JSON Schema is the canonical structural contract; the examples later in this document are presentation guidance only.

Rules:

- Practice reports use `P-###` and never enter the live performance series.
- Live reports use monotonically increasing `Report #001`, `#002`, and so on.
- A frozen report is immutable. Corrections are appended as errata; the original remains available.
- Each report stores the model version, data cutoff, generation time, input snapshot references, code commit, assumptions, ranking, actions, and rationale.
- A material logic change increments the model version and is documented in a changelog.
- Recommended semantic approach: patch for non-decision-affecting corrections, minor for backward-compatible scoring/report additions, major for material methodology changes.
- Backtests of a later model must not be presented as if they were the decisions produced by the earlier model.

## Mistake ledger and postmortems

Every live decision is reviewed at **4, 13, 26, and 52 weeks** using information that became available after the report. Reviews do not rewrite the original decision.

For each horizon, record:

- asset and cash returns, total and annualised where appropriate;
- maximum adverse and favourable excursion;
- whether the original thesis, invalidation condition, and regime assessment were correct;
- whether sizing was proportionate to evidence;
- fees, spread, FX, and tax assumptions versus realised/estimated costs;
- comparison with the #2 and #3 choices and applicable benchmarks;
- opportunity cost of cash or early selling;
- whether the error was data, calculation, interpretation, process, execution, or unavoidable uncertainty;
- one proposed learning, with no model change based on a single anecdote unless it fixes an obvious defect.

The mistake ledger must also capture false positives, false negatives, excessive caution, FOMO, narrative drift, hindsight bias, and any case where the final prose contradicted the deterministic evidence.

## Benchmark “dumb” strategies

The system must compete against simple, investable alternatives using the same contributions, dates, costs, distributions, FX treatment, and available universe:

1. **IVV buy-and-hold:** invest at inception and hold.
2. **IVV DCA:** invest the standard contribution into IVV every Monday or defined contribution Monday.
3. **VAS/VGS diversified DCA:** fixed allocation to VAS and VGS, rebalanced on a declared schedule.
4. **Equal-weight eligible assets:** equal weight across eligible risk assets, with an explicit rule for cash and rebalancing.
5. **5% cash:** retain all funds at the assumed or historically available cash rate.
6. **Simple 50W/200W:** a fully specified moving-average rule, for example risk-on above the selected average and cash below it.
7. **Simple buy-the-dip:** predetermined purchases at documented drawdown bands without discretionary macro analysis.
8. **Allocation without timing:** maintain a strategic multi-asset allocation through regular contributions and periodic rebalancing.

Each benchmark must be defined before results are calculated. Parameters cannot be quietly changed after seeing outcomes.

## Comparison metrics

Report metrics after all applicable costs:

- compound annual growth rate (`CAGR`);
- cumulative and annualised return;
- maximum drawdown and recovery time;
- annualised volatility;
- Sharpe ratio, with the risk-free convention disclosed;
- Sortino ratio, with target return disclosed;
- turnover;
- brokerage, spreads, FX, management fees, and other estimated costs;
- time in cash and average cash balance;
- capital deployed and exposure by asset;
- opportunity cost versus the best simple benchmark;
- **worst regret:** the larger of avoidable missed upside and avoidable downside at the review horizon, calculated using a predeclared formula;
- hit rate by decision/tier, while recognising that hit rate alone can be misleading.

Results should include rolling periods and sensitivity analysis, not only one favourable start/end date.

## Proposed architecture

```text
ChatGPT desktop / Codex subscription
            |
            v
Investment-system plugin
  ├── Skill: Monday workflow, rules, and report format
  └── Local STDIO MCP server
            |
            v
Deterministic Python engine
  ├── Market-data and reference inputs
  ├── Indicators, validation, costs, and scoring
  └── SQLite audit store
            |
            v
Frozen Markdown/JSON reports in Git
```

Responsibilities:

- **ChatGPT/Codex:** provides interactive qualitative reasoning through the operator's subscription and calls the MCP tools when current or stored system data are needed.
- **Plugin skill:** teaches ChatGPT the Monday-only workflow, terminology, hard gates, BTC requirements, report structure, and when each MCP tool is appropriate.
- **Local MCP server:** exposes narrow, typed tools and resources to ChatGPT; validates every request and never relies on model-generated calculations.
- **Market-data API:** prices, corporate/fund data, macro series, sentiment, FX, and fee/reference inputs.
- **Python engine:** validation, weekly aggregation, adjusted-price handling, indicators, cost calculations, benchmark simulation, and reproducible feature snapshots.
- **SQLite:** append-oriented audit store with timestamps, provenance, model versions, decisions, and postmortems.
- **Scoring layer:** deterministic labels, gates, provisional scores, ranking candidates, and sizing eligibility.
- **Frozen reports:** JSON is the machine-readable source of truth and Markdown is the human-readable record. No web dashboard is required.

## Subscription-native MCP operation

### Default profile

The default implementation is designed to run through an eligible **ChatGPT subscription**, without requiring an OpenAI Platform API key or separately billed OpenAI API usage.

The intended Fedora split is explicit: the Fedora home server runs scheduled,
deterministic ingestion, SQLite snapshots, and report drafts; the Fedora
desktop/Codex environment performs qualitative review and explicit freeze
approval. The future MCP runs as a local STDIO process on the review computer,
not as a public server listener. Current setup details must be checked against
the [official MCP documentation](https://learn.chatgpt.com/docs/extend/mcp).

The default profile is:

| Concern | Default choice |
|---|---|
| Qualitative analysis | Interactive Codex/ChatGPT session covered by the operator's eligible subscription |
| ChatGPT integration | Local installable plugin containing a skill and STDIO MCP server |
| Deterministic calculations | Local Python called through the MCP server |
| Persistent records | Local SQLite plus frozen JSON/Markdown in Git |
| Report source of truth | Frozen JSON plus rendered Markdown in Git |
| OpenAI Platform API | Disabled and not required |
| Web hosting | None |
| Trade execution | Manual; never performed by the MCP |

The ChatGPT subscription and OpenAI Platform API are separate products. A subscription must never be assumed to include API credits. If future maintainers add OpenAI API calls, that is an explicit opt-in deployment mode with separate credentials, cost controls, documentation, and model-version impact.

### Portable subscriber setup

Each operator installs an independent local copy:

1. Fork or clone the repository into a private GitHub repository.
2. Open the local project in Codex while signed into an eligible ChatGPT subscription.
3. Install the plugin from its personal/local marketplace entry, or add the MCP server directly in ChatGPT desktop settings during development.
4. Configure the STDIO command to start the repository's MCP server and set its working directory to the cloned repository.
5. Provide market-data configuration through local environment variables or an untracked local `.env`; never put secret values in prompts, reports, fixtures, or Git.
6. Restart ChatGPT/Codex and verify that the investment-system MCP tools are visible.
7. Run the test suite and Practice Report `P-001` end to end.
8. Start the live sequence at `Report #001` only after deterministic and qualitative quality checks pass.

The plugin must be portable: it may not contain absolute paths, another operator's database, credentials, reports, or machine-specific configuration. Fedora Linux is the supported development, test, and production platform; Windows and macOS deployment are out of scope.

### Plugin composition

The installable plugin contains:

- a `.codex-plugin/plugin.json` manifest;
- a focused skill containing the investment-system workflow and reporting rules;
- the registered local MCP connection requirements;
- setup, configuration, and troubleshooting documentation; and
- representative prompts and tests.

OpenAI's plugin documentation permits an installable plugin to contain a skill, an MCP server, or both. The local marketplace is used for personal testing before any wider distribution. See the [official plugin documentation](https://learn.chatgpt.com/docs/build-plugins).

### MCP tools and resources

The initial MCP should expose a small surface:

| Tool | Purpose | Mutation |
|---|---|---:|
| `get_system_status` | Show model version, latest frozen report, data freshness, warnings, and reviews due | No |
| `get_methodology` | Return the relevant versioned rules and definitions | No |
| `refresh_market_snapshot` | Fetch permitted inputs, validate them, and save a candidate snapshot | Yes |
| `calculate_signals` | Compute indicators, classifications, fees, and candidate scores deterministically | Candidate data only |
| `prepare_monday_report` | Assemble a complete draft containing all required fields | Draft only |
| `freeze_report` | Validate and append an immutable live or practice report | Yes; confirmation required |
| `list_reports` | List frozen reports and review status | No |
| `get_report` | Return one frozen report and its provenance | No |
| `run_postmortem` | Calculate a due 4/13/26/52-week review and save a draft | Draft only |
| `freeze_postmortem` | Append an approved review to the mistake ledger | Yes; confirmation required |
| `compare_benchmarks` | Run the declared dumb-strategy comparisons | No permanent mutation |

Resources may expose the versioned methodology, universe, schema, latest validated snapshot, and frozen report archive. They must never expose `.env`, credentials, account identifiers, or unrestricted filesystem contents.

The MCP must not provide `place_trade`, `submit_order`, `transfer_funds`, brokerage-login, or equivalent tools. Trade execution remains outside the system.

### MCP enforcement rules

- `freeze_report` accepts structured fields, not unrestricted prose as the canonical record.
- A live report can be frozen only on an eligible Monday in `Australia/Sydney`; practice reports may run at other times and use `P-###` IDs.
- The server rejects incomplete universe coverage, duplicate ranks, missing BTC BUY/SELL assessments, absent BLAKE2b status, failed critical data checks, or invalid sizing tiers.
- The server calculates indicators, costs, hashes, dates, and gains from the BTC reference basis itself.
- The server never permits the model to overwrite an existing frozen report. Corrections are appended as errata.
- Mutating tools use the narrowest possible inputs, return exactly what changed, and fail closed on ambiguity.
- External source text is treated as untrusted data and cannot alter server instructions or tool rules.
- The server instructions begin with the Monday-only, no-trading, deterministic-calculation, and secret-handling constraints so they are visible during tool selection.

### Operating modes

#### Mode A — subscription-only, recommended for v1.0

This is the simplest and safest initial mode:

1. On Monday, the operator opens ChatGPT desktop or Codex with the plugin enabled.
2. ChatGPT calls the MCP to refresh data, calculate signals, and prepare a candidate structured report.
3. ChatGPT performs the qualitative, source-backed analysis within the interactive subscription session without changing deterministic values.
4. The operator reviews the ranking, BTC BUY/SELL assessments, costs, warnings, and proposed action.
5. After explicit approval, ChatGPT calls `freeze_report`; the MCP writes JSON, Markdown, SQLite records, and the report hash.
6. Any investment order is placed manually outside the system.

This mode has no unattended OpenAI model call, needs no OpenAI API key, and keeps a human review immediately before the report is frozen.

#### Mode B — free-tier deterministic scheduling plus subscription review

An optional GitHub Actions workflow may run the non-LLM data pipeline on a Monday schedule and produce a candidate input snapshot. The operator then opens Codex to complete the qualitative analysis and freeze the report through their subscription.

Rules:

- The scheduled job may fetch permitted market data, validate inputs, compute features, run tests, and create a draft artifact.
- It must not call an OpenAI model unless a separately billed API deployment has been explicitly enabled.
- Set repository spending limits to stop rather than exceed the included allowance.
- Store market-data credentials only in repository action secrets.
- A failed or incomplete scheduled job creates no live report and no implied trade.

#### Mode C — ChatGPT scheduled-task assistance

Where scheduled tasks are available on the operator's plan, they may provide a Monday reminder or prepare research from material accessible to that task. They are not the default execution engine.

Current OpenAI documentation notes that scheduled tasks do not retain access to a local folder or worktree between runs. Therefore a scheduled task must not be designed as though it can silently open the local repository, run its Python engine, or mutate its SQLite database. Required source material must instead be available through the ChatGPT project, uploaded files, or an approved connected service. See the [official scheduled-tasks documentation](https://learn.chatgpt.com/docs/automations).

For v1.0, the scheduled task should say only that Monday's report is due and point the operator to the explicit run procedure. It must not declare or execute an investment decision on its own.

### Zero-additional-cost guardrails

The project targets zero cost beyond an existing eligible ChatGPT subscription, but does not promise permanent free operation. Plan limits and third-party terms can change. Secret-handling requirements are authoritative in the Security section; the following are deployment constraints.

- Do not add an OpenAI API key to the default configuration.
- Run the MCP locally; do not require a web host, custom domain, remote database, or always-on service.
- Use local SQLite and generated JSON/Markdown for persistence.
- Prefer end-of-day or weekly data sources with terms that permit the intended use.
- Do not describe an unverified or rate-limited free quote source as production-grade.
- Keep scheduled jobs small and set a zero spending cap where the provider permits it.
- Record any paid data, API, or infrastructure dependency in `docs/costs.md` before enabling it.
- If a plan or usage limit blocks a run, fail closed: create no live recommendation and preserve the last frozen report unchanged.

### Subscription installation checklist

- [ ] ChatGPT desktop/Codex MCP support is available to the operator.
- [ ] Repository belongs to the new operator and contains no inherited credentials.
- [ ] Local plugin/MCP configuration uses the operator's own repository path and environment.
- [ ] MCP server starts successfully and exposes only the documented tools/resources.
- [ ] OpenAI Platform API is disabled/not configured for the default mode.
- [ ] Local secret storage contains only the minimum required market-data values.
- [ ] No secret is present in prompts, reports, logs, fixtures, plugin files, or Git history.
- [ ] Practice report passes deterministic and qualitative review.
- [ ] Monday timezone and weekly data cutoff are correct.
- [ ] Failed-run behavior leaves the last live report unchanged.
- [ ] Reports display a clear research/not-financial-advice notice.
- [ ] Trade execution remains manual.

## Proposed repository structure

```text
investment-decision-system/
├── README.md
├── LICENSE
├── pyproject.toml
├── .env.example                 # names only; never real secrets
├── .gitignore
├── .github/
│   └── workflows/
│       └── monday-snapshot.yml  # deterministic only; no model API by default
├── plugin/
│   ├── .codex-plugin/
│   │   └── plugin.json
│   └── skills/
│       └── monday-investment-system/
│           └── SKILL.md
├── config/
│   ├── universe.yaml
│   ├── model-v1.0.yaml
│   ├── data-sources.yaml
│   └── benchmarks.yaml
├── src/investment_system/
│   ├── ingestion/
│   ├── validation/
│   ├── indicators/
│   ├── overlays/
│   ├── scoring/
│   ├── costs/
│   ├── benchmarks/
│   ├── reporting/
│   ├── storage/
│   └── mcp_server.py
├── migrations/
├── schemas/
│   └── frozen-report.schema.json
├── templates/
│   └── monday-report.md.j2
├── data/
│   ├── README.md
│   └── .gitkeep                 # database/raw caches ignored by default
├── reports/
│   ├── practice/
│   ├── live/
│   ├── errata/
│   └── postmortems/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── mcp_contract/
│   ├── fixtures/
│   └── golden-reports/
├── docs/
│   ├── methodology.md
│   ├── data-dictionary.md
│   ├── model-changelog.md
│   ├── mistake-ledger.md
│   ├── subscription-installation.md
│   ├── mcp-tools.md
│   ├── costs.md
│   └── security.md
└── scripts/
    ├── generate_monday_report.py
    ├── run_postmortems.py
    └── run_benchmarks.py
```

## Structured frozen-report schema

JSON is the canonical machine-readable artifact; Markdown is its human-readable rendering. The maintained canonical schema is `schemas/frozen-report.schema.json`; the following is a conceptual field map for readers and must not supersede the repository schema. Values are illustrative placeholders, not a current recommendation.

```json
{
  "schema_version": "1.0",
  "report_id": "001",
  "report_kind": "live",
  "model_version": "1.1",
  "decision_date": "2026-09-07",
  "timezone": "Australia/Sydney",
  "data_cutoff": "2026-09-07T08:00:00+10:00",
  "generated_at": "2026-09-07T08:05:00+10:00",
  "code_commit": "<git-commit>",
  "input_snapshot_id": "<snapshot-id>",
  "assumptions": {
    "cash_yield_pct": 5.0,
    "btc_reference_basis_usd": 60000,
    "broker_terms_verified_at": "<timestamp>",
    "price_adjustment_method": "<method>"
  },
  "rankings": [
    {
      "rank": 1,
      "asset": "<asset>",
      "new_money_action": "A$0|A$999|A$2000|A$4000|BTC_EQUIVALENT",
      "existing_position_action": "HOLD|CONSIDER_PARTIAL_SELL|PARTIAL_SELL|EXIT",
      "confidence": "high|medium|low|insufficient",
      "valuation": "<label>",
      "technical_stretch": "<label>",
      "trend": "<label>",
      "regime": "<label>",
      "waiting_risk": "low|medium|high|not_applicable",
      "score": null,
      "hard_gates_passed": true,
      "rationale": "<concise rationale>"
    }
  ],
  "features": {
    "<asset>": {
      "currency": "AUD|USD",
      "weekly_close": null,
      "ma_20w": null,
      "ma_50w": null,
      "ma_200w": null,
      "distance_20w_pct": null,
      "distance_50w_pct": null,
      "distance_200w_pct": null,
      "rsi_weekly": null,
      "macd_line_weekly": null,
      "macd_signal_weekly": null,
      "macd_histogram_weekly": null,
      "ath": null,
      "drawdown_from_ath_pct": null
    }
  },
  "sentiment": {
    "equity_fear_greed": {"value": null, "category": null, "provider": null, "effective_at": null},
    "crypto_fear_greed": {"value": null, "category": null, "provider": null, "effective_at": null}
  },
  "bitcoin": {
    "cycle_prior": "bear",
      "buy_assessment": {"decision": "NO_BUY", "confidence": "insufficient", "rationale": "Conceptual placeholder; use the canonical schema and evidence-backed assessment."},
      "sell_assessment": {"decision": "HOLD", "confidence": "insufficient", "rationale": "Conceptual placeholder; use the canonical schema and evidence-backed assessment."},
    "price_usd": null,
    "gain_from_60000_basis_pct": null,
    "blake2b_gate": {"status": "unavailable", "reason": "<status and source reference>"}
  },
  "selected_decision": {
    "asset": "CASH",
    "amount_aud": 0,
    "order_type": null,
    "estimated_brokerage_aud": 0,
    "estimated_spread_aud": null,
    "estimated_fx_aud": 0,
    "decision_reason": "<reason>",
    "invalidation_conditions": ["<condition>"]
  },
  "sources": [
    {"source_id": "<id>", "title": "<title>", "url": "<url>", "retrieved_at": "<timestamp>"}
  ],
  "quality_control": {
    "checks_passed": [],
    "warnings": [],
    "missing_fields": [],
    "secret_scan_passed": true
  },
  "report_hash": "<sha256-of-canonical-json>"
}
```

The repository schema and business validator now enforce the structural and cross-field rules. Any future field or enum change must be made in the canonical schema first and then reflected here only as explanatory documentation.

## Sample Monday report

The following is a format example only. It is **not Report #001 and contains no live recommendation**.

```markdown
# Monday Investment Report #___ — YYYY-MM-DD

Model: v__  
Data cutoff: YYYY-MM-DD HH:MM Australia/Sydney  
Status: FROZEN / PRACTICE

## Decision

**#1 <asset> — <A$0 / A$999 / A$2,000 / A$4,000>**

One-paragraph decision, including why it clears or fails the cash hurdle.

## Top three

| Rank | Asset | Valuation | Technical | Regime | Waiting Risk | Confidence | Action |
|---:|---|---|---|---|---|---|---|
| 1 | ... | ... | ... | ... | ... | ... | ... |
| 2 | ... | ... | ... | ... | ... | ... | ... |
| 3 | ... | ... | ... | ... | ... | ... | ... |

## Full universe

One row per IVV, NDQ, VAS, VGS, IZZ, VAE, gold, BTC, and cash.

## Selected asset analysis

- Fundamental/macro valuation:
- Technical stretch and trend:
- Regime:
- Asset-specific overlay:
- Cash comparison:
- Costs:
- Thesis and invalidation:

## Bitcoin

**BTC BUY:** <assessment>  
**BTC SELL:** <assessment>  
Reference basis: US$60,000  
Four-year-cycle prior: <state/evidence>  
BLAKE2b: <material update or standard no-change statement>

## Costs and execution

Expected brokerage, spread, FX, management fee, liquidity, and tax notes.

## Risks, contrary case, and confidence

What could make the decision wrong, what evidence is missing, and what would change the conclusion.

## Quality-control record

Data sources/times, completed checks, warnings, commit, snapshot, and report hash.

## Review schedule

4-week: YYYY-MM-DD  
13-week: YYYY-MM-DD  
26-week: YYYY-MM-DD  
52-week: YYYY-MM-DD
```

## Current open questions

### Decisions already made

- The current model/configuration is Model v1.0.
- Weekly RSI uses Wilder smoothing in the implemented indicator contract.
- BTCB2 is **not** in the universe. A prior version (v1.1) added it on
  operator authorization; that has been withdrawn, the model reverted to
  v1.0, and BTCB2 is now tracked only as a candidate against the crypto
  asset inclusion gate's six concrete criteria (see "Crypto asset
  inclusion gate"). There is no blanket ban on non-BTC cryptocurrencies —
  BTCB2 is simply the only candidate currently under consideration.
- Fedora is the supported development, test, and production platform; Windows
  and macOS deployment are out of scope.
- Discord is not an approved data source for this system.
- This project is developed by a single coding agent (Claude Code); the
  earlier two-agent (Claude Code + Codex) build split has ended. See
  `docs/archive/` for that phase's coordination log and design reviews,
  retained as historical record.
- **Gold's vehicle is ASX:GOLD (Global X Physical Gold, unhedged)** in AUD —
  operator decision, 2026-09-07, after comparing it against QAU (BetaShares,
  currency-hedged, higher fee, no diversification benefit against AUD
  weakness) and ruling out PMGOLD (unreliable market-data feed) and NUGG
  (too little trading history for a 200-week moving average). See
  [Ingestion](docs/wiki/ingestion.md) for the data-quality comparison and
  [Changelog](docs/wiki/changelog.md) for the full reasoning.
- Market-data provider for ASX equities and gold: **Yahoo Finance's
  unofficial chart endpoint**, after Finnhub (blocked on the operator's
  plan), Alpha Vantage (no real ASX coverage), Twelve Data (US-only free
  tier), and Stooq (bot-walled) were all empirically ruled out. See
  [Ingestion](docs/wiki/ingestion.md).

### Remaining questions

1. What exact cash product and after-tax/after-fee yield should replace the flat 5% assumption?
2. What is the weekly bar cutoff for ASX assets versus globally traded BTC and gold?
3. ~~Which market-data providers are authoritative for adjusted ASX history, fundamentals, macro, ATH, and sentiment?~~ Resolved for ASX/gold price history: Yahoo Finance (see "Decisions already made"). Fundamentals, macro, and sentiment providers remain open.
4. What exact MACD parameters will Model v1.0 freeze beyond the currently implemented indicator contract?
5. ~~How should gold be implemented: spot reference, ASX ETF, or another vehicle, and in which currency?~~ Resolved: ASX:GOLD (Global X Physical Gold, unhedged), AUD — see "Decisions already made".
6. What are the portfolio's existing weights, contribution schedule, concentration limits, liquidity needs, and maximum acceptable drawdown?
7. Does “one asset per Monday” remain optimal when diversification or brokerage rules favour multiple orders?
8. What hard gates and score thresholds map to each sizing tier?
9. How should Waiting Risk be measured without merely rewarding recent momentum?
10. What evidence formally overturns the BTC bear-cycle prior?
11. ~~What exact operational/liquidity thresholds satisfy the crypto asset inclusion gate?~~ Resolved: see the six-point establishment gate above. Open sub-question: are US$250,000/3 months/two-venue/5% thresholds the right numbers, or should the operator recalibrate them before BTCB2 (or any candidate) is actually assessed against them?
12. What partial-sale percentages and tax constraints apply to BTC SELL decisions?
13. How should dividends, distributions, franking credits, FX, and taxes be treated in benchmarks?
14. What formula defines worst regret without creating hindsight-driven optimisation?
15. What emergency, non-Monday risk rule—if any—is justified?

## Roadmap

### Phase 0 — freeze the specification

- Resolve the open parameters required for Model v1.0.
- Define the universe, instruments, currencies, data cutoff, costs, and security policy.
- Create the JSON Schema, data dictionary, model changelog, and report template.

### Phase 1 — deterministic data foundation

- Implement API adapters and immutable raw snapshots.
- Build weekly aggregation, adjusted-price validation, indicators, ATH, FX, fee, and sentiment calculations.
- Add SQLite migrations, provenance, missing-data rules, and automated secret scanning.
- Test calculations against independent references and golden fixtures.

### Phase 1.5 — local MCP and plugin baseline

- Build and test the local STDIO MCP server with the narrow tool surface defined above.
- Create the installable plugin and workflow skill.
- Document Mode A as the default and ensure it requires no OpenAI Platform API key.
- Add portable installation instructions and environment-variable setup.
- Add the optional deterministic-only GitHub Actions workflow with a zero spending cap recommendation.
- Test failure behavior so missing data or exhausted plan limits cannot create a live decision.
- Complete one portable setup rehearsal using a clean clone with no inherited paths, database, or secrets.
- Test representative ChatGPT prompts and verify every MCP response against the deterministic engine.

### Phase 2 — Model v1.0 and Report #001

- Freeze provisional component definitions, hard gates, and tier eligibility.
- Generate a dry run and reconcile every value manually.
- Produce **Report #001 / Model v1.0** for the first upcoming Monday, intended to be **7 September 2026**, only after data and quality checks pass.
- Store canonical JSON, rendered Markdown, commit, input snapshot, and hash.

### Phase 3 — audit and review workflow

- Add MCP queries for rankings, history, exposure, upcoming reviews, and the mistake ledger.
- Automate 4/13/26/52-week postmortem reminders and calculations.
- Ensure report inputs and warnings remain traceable in Markdown, JSON, and ChatGPT responses.

### Phase 4 — benchmark and validation

- Implement all dumb strategies with equal cash flows and realistic costs.
- Run walk-forward and rolling-period tests with no look-ahead.
- Compare CAGR, drawdown, volatility, Sharpe/Sortino, turnover, costs, cash time, opportunity cost, and worst regret.
- Document sensitivity and failure modes; avoid optimising solely for historical CAGR.

### Phase 5 — controlled improvement

- Review aggregate evidence at defined intervals rather than changing the model after every outcome.
- Version every material change and rerun out-of-sample/forward comparisons.
- Keep the simplest model that remains useful, auditable, and competitive with dumb benchmarks.

## Security and repository hygiene

- Store credentials only in an approved secrets manager or untracked local environment file.
- Commit `.env.example` with variable names and documentation only—never values.
- Ignore databases, raw licensed data, local caches, generated credentials, and account exports unless deliberately sanitised.
- Redact broker account data and personal identifiers from reports and screenshots.
- Run a secret scan before every release and before making the repository public.
- If a secret is ever committed, revoke/rotate it first; deleting it from the latest commit is not sufficient.
- Treat a ChatGPT subscription login as an interactive user identity, not as an API credential to extract, copy, or embed.
- Never attempt to automate a subscription session by scraping cookies, browser storage, or account tokens.
- Never expose unrestricted filesystem access through the MCP; allow only declared configuration, data, report, and database locations inside the project.

---

This document defines the intended system. It does not retroactively convert Practice Reports P-001 or P-002 into live records. The permanent live scorecard begins only when **Report #001 / Model v1.0** is frozen on an eligible Monday.
