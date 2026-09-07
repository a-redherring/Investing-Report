# Configuration reference

Loaded by [`src/investment_system/config.py`](../../src/investment_system/config.py).
Both files are read fresh on every call — there is no caching, so editing the YAML
takes effect on the next run with no code change required.

## `config/model-v1.0.yaml`

```yaml
model_version: "1.0"
cash_yield_pct: 5.0
brokerage:
  minimum_aud: 11.0
  rate_pct: 0.10
  qualifying_buy_limit_aud: 999.0
```

| Field | Used by | Meaning |
|---|---|---|
| `model_version` | `config_snapshot()` output only (informational) | Identifies which model version's rules this file encodes. Bump it whenever a change here would alter a past decision — see [Changelog](changelog.md). |
| `cash_yield_pct` | Not yet consumed by any calculation | The assumed annual cash yield used as the hurdle rate in the design doc. Currently exposed only via `investment-system config`; no scoring/hurdle logic reads it yet (that layer isn't built — see [Architecture](architecture.md)). |
| `brokerage.minimum_aud` | `engine.cost_table()` → `costs.asx_brokerage()` | Flat-dollar minimum brokerage charged on a non-qualifying ASX order. |
| `brokerage.rate_pct` | same | Percentage-of-order brokerage rate; the actual fee is `max(minimum_aud, amount * rate_pct / 100)`. |
| `brokerage.qualifying_buy_limit_aud` | same | An order at or below this amount is treated as a qualifying buy (currently: A$0 brokerage) — see `costs.asx_brokerage`'s `qualifying_buy` argument. |

**Important:** these are the working assumptions used for indicative sizing, not
verified broker terms. Per the design doc, actual CMC Invest AU terms must be
re-checked before any live decision that relies on them.

## `config/universe.yaml`

```yaml
assets:
  - {symbol: IVV, currency: AUD, core: true}
  - {symbol: NDQ, currency: AUD, core: false}
  - {symbol: VAS, currency: AUD, core: true}
  - {symbol: VGS, currency: AUD, core: true}
  - {symbol: IZZ, currency: AUD, core: false}
  - {symbol: VAE, currency: AUD, core: true}
  - {symbol: GOLD, currency: AUD, core: false}
  - {symbol: BTC, currency: USD, core: false}
  - {symbol: CASH, currency: AUD, core: false}
```

Each entry: `symbol` (matched against the `asset` column in the weekly price CSV,
case-insensitive — `engine.load_prices()` upper-cases it), `currency` (informational;
nothing currently converts between currencies), `core` (whether the asset gets the
core/Waiting-Risk treatment described in the design doc — not yet used by any
calculation). `GOLD`'s underlying vehicle is ASX:GOLD (Global X Physical Gold,
unhedged) — see [Ingestion](ingestion.md#gold-vehicle-selection-goldax) for the
decision and the data-quality comparison against the other ASX gold ETFs.

Per the design doc, this universe is closed by default: adding an asset here should
come with a `model_version` bump and the accompanying documentation described in
[Changelog](changelog.md), not a silent edit. **BTCB2 is deliberately not here.**
A prior version (v1.1) added it with `instrument_type`, `reference_pair`,
`venue`, and `status` fields recording a since-reverted exchange listing;
that inclusion was withdrawn and the model reverted to v1.0. There's no blanket
ban on non-BTC cryptocurrencies, but BTCB2 (the only candidate currently
under consideration) is tracked in `INVESTMENT_DECISION_SYSTEM.md`'s crypto
asset inclusion gate until it independently clears six concrete criteria
(operational maturity, multi-venue liquidity, price discovery, custody,
independent verifiability, and a defined thesis) — see
[`docs/candidates/BTCB2.md`](../candidates/BTCB2.md) for current status
against each.

## Portability (non-editable installs)

`load_model_config()`/`load_universe()` (and `schema.load_schema()`) resolve
their file's directory fresh on every call via `config.resolve_repo_root()`,
checked in this order:

1. **`INVESTMENT_SYSTEM_CONFIG_DIR`** environment variable, if set — an
   explicit override, config only (there's no schema-specific env var; the
   schema always resolves via steps 2–3).
2. A `config/` (or `schemas/`) directory under the current working directory,
   or one of its parents — the documented workflow: run commands from within
   a clone of this repository (or a subdirectory of one).
3. The path relative to this installed package
   (`Path(__file__).resolve().parents[2]`) — works for an editable/source
   install (`pip install -e .`) regardless of cwd.

A non-editable wheel install run from outside any repo checkout, with no env
var set, fails closed with an actionable `FileNotFoundError` listing every
directory it checked — it does not silently read nothing or crash with a bare
"file not found" three frames deep in YAML parsing. Set
`INVESTMENT_SYSTEM_CONFIG_DIR=/path/to/clone/config` in that case (e.g. for an
MCP server pointed at an operator's own clone, per the design doc's deployment
model).

## How to change these safely

1. Edit the YAML.
2. Run `investment-system config` and confirm the parsed output looks right.
3. Run `make test` — `tests/test_config.py` asserts the exact values currently
   committed, so a real parameter change will fail that test until you update it.
4. Update this page if you added/removed/repurposed a field.
5. Add a [Changelog](changelog.md) entry.
