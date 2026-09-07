# BTCB2 — crypto asset inclusion gate tracking

**Status: candidate only.** BTCB2 is not in `config/universe.yaml`, not
ranked, and not sized. This file tracks its progress against the six-point
crypto asset inclusion gate defined in
[`INVESTMENT_DECISION_SYSTEM.md`](../../INVESTMENT_DECISION_SYSTEM.md#crypto-asset-inclusion-gate).
Nothing in this file is a verified fact until it is independently sourced
here **and** reproduced with sources in an actual Monday report — report
generation doesn't exist yet (see the [roadmap](../wiki/roadmap.md)), so
right now this file is the only place any of this is recorded at all.

An empty/`TODO` field means **not yet demonstrated**, not "assumed true" —
the gate requires all six to hold, with sources, across four consecutive
Monday reports before a model-version change can propose adding BTCB2, and
nothing here substitutes for that. As of 2026-09-07: criteria 4, 5, and 6
pass; 1 fails outright; 2 and 3 remain unsourced.

## 1. Operational maturity

- **Requirement:** mainnet live ≥3 months, no unresolved consensus-halting
  incident during that period.
- **Status:** TODO. Known baseline as of 2026-09-06: mainnet launched
  2026-08-30 (block 961,640) — roughly one week old, well short of the
  3-month bar.
- **Evidence / source:** [crypto.news](https://crypto.news/bitcoin-blake2b-fork-faces-sept-1-launch-test/), [cryptonews.net](https://cryptonews.net/news/bitcoin/33369611/)
- **Last reviewed:** 2026-09-06

## 2. Liquidity

- **Requirement:** ≥US$250,000 trailing-30-day average daily volume,
  aggregated across ≥2 independent, non-affiliated exchanges. Neoxa alone
  never satisfies this.
- **Status:** TODO
- **Evidence / source:** TODO
- **Last reviewed:** TODO

## 3. Price discovery

- **Requirement:** ≥2 independent venues quote the reference pair, <5%
  price divergence between them at time of check.
- **Status:** TODO
- **Evidence / source:** TODO
- **Last reviewed:** TODO

## 4. Custody

- **Requirement:** a self-custody path via open-source wallet software, or
  support from a recognized third-party custodian/hardware-wallet vendor.
  Exchange-only custody (Neoxa included) does not satisfy this.
- **Status:** PASS.
- **Evidence / source:** Operator-verified directly (2026-09-07): BTCB2 is a
  straight fork of Bitcoin with only the PoW algorithm changed, so wallet
  software already used for BTC (address format, key derivation) works
  identically for BTCB2. The operator confirmed this personally rather than
  relying on a claim from the project itself. Note on evidentiary form: a
  custody setup is inherently a private, first-person fact — per this
  project's own rule that no account identifier or custody detail belongs
  in a public artifact, this is recorded as operator attestation rather
  than a public source, unlike criteria 1-3 which should be independently,
  publicly checkable.
- **Last reviewed:** 2026-09-07

## 5. Independent verifiability

- **Requirement:** a public block explorer and node software independent of
  any single exchange.
- **Status:** PASS.
- **Evidence / source:** Operator-verified directly (2026-09-07): runs an
  independent BLAKE2b node (not Neoxa-hosted), used to verify chain state
  and custody directly rather than trusting a single exchange's word for
  it. Same evidentiary-form note as criterion 4 above.
- **Last reviewed:** 2026-09-07

## 6. Defined thesis and risk model

- **Requirement:** a written, dated investment thesis and explicit
  invalidation conditions, addressing plausibility and risk modelling
  against the vulnerabilities the candidate responds to.

**Scope note:** this section is deliberately about the *concept* —
whether the structural vulnerabilities BTCB2 responds to are real — not
about whether BTCB2 itself currently satisfies criteria 1-5 above (it
doesn't, per the operational-maturity status alone). Those stay tracked
separately. Venue/exchange-specific risk (Neoxa) is explicitly **not**
included here pending better-sourced evidence than currently exists;
it belongs under criteria 2/4 once that evidence is gathered.

### Background (settled facts, not part of the argument itself)

- Bitcoin Core v30 removed the historical 80-byte default OP_RETURN relay
  limit (proposed by Peter Todd at Chaincode Labs' request) — data larger
  than 80 bytes is now relayed and mined by default rather than requiring a
  workaround. ([TradingView/Cointelegraph](https://www.tradingview.com/news/cointelegraph:953d13016094b:0-bitcoin-core-to-unilaterally-remove-controversial-op-return-limit/))
- **BIP-110** ("Reduced Data Temporary Softfork") responded to this,
  motivated centrally by spam and CSAM risk, not a generic data-bloat
  complaint. It required 55% miner signaling to activate; actual support
  never approached that — reported miner/hashrate signaling ranged from
  0.31% to 2.53% of hashrate across different snapshots (sources disagree
  on the exact figure; both are far below threshold), while node-level
  support was higher but still a minority: ~2-8% of listening nodes
  specifically signaled for BIP-110, against a broader ~22.65% of nodes
  running Bitcoin Knots generally (running Knots does not automatically
  mean signaling for BIP-110). A chain split was triggered at block
  961,632 (2026-08-08); the minority chain mined two blocks in eight hours
  and stalled, inheriting full network difficulty with almost none of the
  hashrate (next retarget estimated ~350 days out). ([BIT](https://www.bit.com/knowledge-hub/bip-110), [KuCoin](https://www.kucoin.com/blog/bitcoin-bip-110-failure-explained), [KuCoin flash](https://www.kucoin.com/news/flash/bitcoin-bip-110-fork-fails-as-mainnet-outpaces-minority-chain-by-26-blocks))
- **BTCB2 / "Bitcoin BLAKE2b"** is Bitcoin Knots' own direct follow-through
  on BIP-110's failure, not an unrelated opportunistic project: hard fork
  to BLAKE2b proof-of-work at block 961,640 (2026-08-30), locked in by
  Knots release 29.4.1rc5 (2026-09-01). Led by **Luke Dashjr** (long-tenured
  Bitcoin Core contributor, Bitcoin Knots maintainer) and **Chris Guida**.
  Dashjr resigned as chairman, CTO, and director of mining pool Ocean on
  2026-08-29 (equity repurchased by parent Mummolin) explicitly over
  disagreement on Bitcoin mining's future/BIP-110, and is launching a new
  venture, Convoy, tied to the BLAKE2b effort. ([CoinDesk](https://www.coindesk.com/business/2026/08/31/luke-dashjr-exits-mining-pool-ocean-after-split-over-bitcoin-mining-s-future), [crypto.news](https://crypto.news/bitcoin-mining-divide-pushes-luke-dashjr-out-of-ocean/), [cryptonews.net](https://cryptonews.net/news/bitcoin/33369611/))
- The project's own stated rationale (bitcoin-blake2b.org) is about
  blocking large SHA256d miners from monetizing arbitrary data storage at
  node operators' expense — **not** the "whitepaper mandates a PoW change
  when regulated agencies hold majority hashrate" argument originally
  presented to the operator.
- **Closed item:** checked directly against the Nakamoto whitepaper text
  (kept alongside this file at [`bitcoin.pdf`](bitcoin.pdf), the canonical
  source, so this can be re-checked without re-fetching it) — it contains
  no statement requiring a PoW change if regulated agencies gain majority
  hashrate, and "honest nodes" is defined purely behaviorally, indifferent
  to operator identity/regulatory status. The whitepaper citation neither
  supports nor opposes the thesis; it carries no further weight and isn't
  discussed again below.

### The conceptual thesis

**Mining concentration and rule-change risk — open, not settled.** Current
reported pool concentration: Foundry + AntPool combined variously reported
at 41-48% depending on snapshot (34.2%+14.2% in May 2026 vs. 23.8%+17.3% in
late August 2026); top 4 pools (Foundry, AntPool, ViaBTC, F2Pool) ~70-73%;
Nakamoto Coefficient of 3. ([Hashrate Index](https://hashrateindex.com/blog/top-10-bitcoin-mining-pools-of-2026/), [Squared Tech](https://www.squaredtech.co/bitcoin-mining-pools-in-2026-the-top-4-control-70-of-hashrate))
The standard counter-argument is that no majority-hashrate soft or hard
fork can seize or alter existing balances without the owner's signature —
economic-majority nodes would simply reject an illegitimate rule change,
producing an orphaned minority fork rather than a successful capture. **That
counter-argument assumes economic-majority actors (exchanges, custodians,
index/ETF providers) actively verify and enforce rule continuity rather
than simply following whichever chain the market treats as "real BTC."**
Given the culture-erosion evidence below, that assumption is not obviously
safe. If a rule change (demurrage-style, a supply-cap change, or similar)
achieved near-universal mining support, and economically significant actors
simply relisted/repriced that chain as "BTC" by default, the
rule-preserving original chain could become the economically irrelevant
side — technically correct, practically a larp. **This is flagged as an
open question requiring further evidence, not resolved either way.**

**Censorship "delay" can become a functional block.** A minority of
non-complying hashrate does not guarantee forbidden transactions confirm in
practical time. Expected wait time scales inversely with the willing
hashrate share: if compliance pressure (regulatory or reputational) extends
beyond the top 2 pools to most large, identifiable, jurisdiction-exposed
operators — plausible, since being large and identifiable correlates with
being regulatable in any jurisdiction — the residual willing hashrate could
shrink enough that expected confirmation time becomes impractical for
real-world use, which is a functional block even without being a
mathematically absolute one. Historical precedent for compliance-driven
filtering already exists at smaller scale: F2Pool (~11% of hashrate)
documented excluding OFAC-sanctioned-address transactions in January 2025;
Marathon Digital's 2021 OFAC-compliant pool was reversed after community
backlash, showing the check exists but is not guaranteed to hold.
([Finbold](https://finbold.com/third-largest-bitcoin-mining-pool-likely-censored-ofac-sanctioned-transactions/), [The Block](https://www.theblock.co/post/104263/an-ofac-compliant-bitcoin-miner-revives-debate-about-transaction-censorship))

**CSAM — a moral/ethical priority, not merely an economic risk calculus.**
Independent academic research has found illegal content, including
CSAM-related material, already embedded via OP_RETURN/Coinbase fields on
the actual SHA256d chain (this predates and is separate from the more
severe, well-documented BSV case, where the absence of any block-size/data
limit made bulk storage economically trivial). Legal commentary on Bitcoin
Core v30 specifically calls the *marginal* liability risk to ordinary node
operators "overblown," on the reasoning that the underlying exposure
predates v30 and isn't meaningfully changed by removing a symbolic relay
limit a determined actor could always route around. ([Protos](https://protos.com/exclusive-lawyers-call-bitcoin-core-v30-csam-concerns-overblown/))
**The operator's stated position is that this legal-risk-magnitude framing
does not resolve the concern**: once the line has been crossed — illegal
content demonstrably exists on-chain, and full node operators are, by the
protocol's own design, storing and relaying it merely by validating —
this becomes a moral, ethical, and (for some) religious question that
takes precedence over an economic/legal probability calculus. Any credible
step that reduces this exposure is treated as valuable on those grounds
independent of how "likely" prosecution or civil liability is judged to be.
This is recorded as the operator's explicit ethical stance, not asserted as
an objective, universally agreed fact — but it is a legitimate and
material input to this thesis.

For **regulated miners specifically (AntPool, Foundry)**: CSAM exposure is
a sharper, more urgent, already-live incentive to filter block contents
than OFAC-sanctions compliance — criminal exposure for named, identifiable
corporate entities, not a sanctions-list technicality. This gives these
firms an independent, non-ideological reason to build content-filtering
into block construction regardless of any new law, which feeds back into
both the mining-concentration point above and the general trajectory of
increasing miner-level content control this thesis is concerned with.

**Node-running, not just self-custody, is the load-bearing culture
metric.** Self-custodied Bitcoin exceeds $800B (~66% of circulating
supply) and is reportedly resilient, partly driven by distrust of
custodial platforms. ([KuCoin](https://www.kucoin.com/news/flash/self-custodied-bitcoin-holdings-surpass-800-billion-triple-etfs-and-treasuries))
This is **not** treated as an independent counterweight to node-count
decline, because holding your own keys does not mean independently
verifying your own balance and the rules your coins were validated under —
per the whitepaper's own Simplified Payment Verification section, a user
without their own full node is trusting someone else's validation. Most
self-custodying individuals almost certainly rely on third-party
nodes/explorers/wallet backends rather than running their own node, so the
self-custody figure likely overstates how intact the "don't trust, verify"
culture actually is. The more load-bearing (and more concerning) signal is
the observed neglect of node-counting infrastructure itself (e.g.
Bitnodes.io's domain lapsing in May 2026) and the absence of any comparably
strong growth story for full-node operation, set against real, dated
erosion at the institutional/cultural center: Michael Saylor — by most
measures the single most influential institutional Bitcoin voice — publicly
reversed his prior "no other token gains institutional acceptance" stance
to endorse Solana and Ethereum for "digital credit" infrastructure at
Strategy World 2026, a genuine crack in strict maximalism from its most
prominent proponent (who is also on record opposing BIP-110 itself).
([Yahoo Finance](https://finance.yahoo.com/news/michael-saylor-unveils-digital-credit-110031292.html))

**Exit vs. voice.** Dashjr and Guida chose to fork away rather than
continue arguing within mainline Bitcoin after losing the BIP-110 vote.
Read generously, this is evidence *against* "price over principle" (they
gave up Bitcoin's liquidity, security budget, and network effects entirely
to make a point). Read more cautiously, repeated instances of the most
principle-driven contributors choosing exit over voice could gradually
concentrate the remaining mainline community toward institutional/price-
focused actors — a slow, contingent pattern, not proven by one fork, but
consistent with the Saylor shift happening at the same time from the
opposite direction (someone who stayed, and whose principles moved).

**Why this matters held over a long horizon.** None of the above describes
an imminent failure of mainline Bitcoin. The argument is compounding, not
immediate: over a multi-decade holding horizon, small-probability
structural risks (majority-rule capture facilitated by eroding
economic-majority enforcement, censorship creep, continued mining
concentration, unresolved CSAM exposure) accumulate in a way they would not
for a short holding period. That is the stated basis for taking these
concerns seriously enough to consider a hedge, not a claim that any of this
is likely to materialize soon.

### Invalidation conditions

Concrete, checkable conditions that would mean this thesis is wrong or has
become moot — stated in advance, and to be checked against real data as it
becomes available:

1. **Mining decentralizes rather than concentrates.** The Nakamoto
   Coefficient for Bitcoin mining rises (fewer entities needed to reach a
   hashrate majority shrinks the risk, a rising coefficient means more
   entities are needed) and stays elevated over a sustained period, rather
   than continuing to sit at or near 3.
2. **Stratum V2 (or an equivalent) demonstrably prevents pool-level
   censorship in a real, observed incident** — i.e., individual miners
   overriding a pool operator's exclusion of a transaction actually happens
   in practice, not just in protocol theory.
3. **An attempted majority-hashrate rule change is firmly and durably
   rejected by economic-majority actors** — exchanges, custodians, and
   major wallets refusing to relist or honor a rule-violating chain as
   "real BTC," rather than following it by default. (The absence of any
   such attempt is not itself evidence either way; this requires an actual
   tested instance.)
4. **Full-node / validation metrics stabilize or recover**, with adequate
   measurement infrastructure restored, rather than continuing to erode or
   remaining unmeasurable.
5. **CSAM/illegal-content exposure on mainline Bitcoin is durably reduced**
   via an enforceable mechanism (a successful soft fork, universally
   adopted filtering, or equivalent) — reducing the moral/ethical urgency
   that motivates part of this thesis.
6. **BTCB2 (or a comparable alternative) fails to gain any meaningful
   adoption over a long period despite the underlying vulnerabilities
   persisting** — if the concept is sound but the market never responds to
   it even as the risk remains live, that is itself information worth
   weighing against continued conviction.

Any of these substantially undermines the corresponding part of the thesis
above; several holding simultaneously would undermine it materially.

- **Status:** PASS. The requirement is that a written thesis and explicit
  invalidation conditions *exist* — a plausibility and risk-modelling
  exercise against the vulnerabilities discussed above, not a claim that
  BTCB2 will succeed or that any of the above is proven correct. That
  requirement is met as of this entry. This is not a one-time pass: each
  future report (once report generation exists) should check current
  conditions against the six invalidation conditions above and flag if any
  are met — which would put this criterion, and the thesis generally, back
  into question and require re-assessment, not a rewrite of this entry from
  scratch.
- **Last reviewed:** 2026-09-07

## Overall gate status

| # | Criterion | Status |
|---|---|---|
| 1 | Operational maturity | **FAIL** — ~1 week old, needs ≥3 months; reassess over time |
| 2 | Liquidity | TODO — unsourced |
| 3 | Price discovery | TODO — unsourced |
| 4 | Custody | **PASS** — operator-verified directly (2026-09-07) |
| 5 | Independent verifiability | **PASS** — operator-verified directly (2026-09-07) |
| 6 | Defined thesis and risk model | **PASS** — thesis and invalidation conditions defined (2026-09-07); recheck against invalidation conditions every future report |

**All six must hold, with sources, across ≥4 consecutive Monday reports**
before a model-version change can propose adding BTCB2 to
`config/universe.yaml`. Update this file as evidence is gathered; add a
[changelog](../wiki/changelog.md) entry whenever this file's status changes.
