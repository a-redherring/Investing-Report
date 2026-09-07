"""Deterministic feature assembly: one candidate record per universe asset.

Combines what's actually computable today (indicators.py's technical
snapshot from weekly price data) with an honest placeholder for the two
required layers that have no data source at all yet -- fundamental
valuation and regime (see INVESTMENT_DECISION_SYSTEM.md's three-layer
model). This is NOT a ranking or a score: nothing here decides
new_money_action, sizing, or rank -- that's deferred until component
weights and hard-gate thresholds are decided (see the roadmap). It only
assembles the inputs a future scoring step would consume.

Because valuation and regime are entirely unimplemented -- not merely
uncertain, but structurally absent -- every candidate's confidence and
hard_gates_passed are forced to their fail-closed values ("insufficient",
False) regardless of how complete the technical data is. This isn't a
guessed threshold; it's the direct consequence of the design doc's own
"missing critical data forces no trade" rule applied to two of the three
required layers. It changes automatically once those layers are built.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .config import load_universe
from .engine import load_prices
from .indicators import calculate

NO_VALUATION_SOURCE = "Insufficient Data"
NO_REGIME_SOURCE = "Unclear"


@dataclass(frozen=True)
class Candidate:
    symbol: str
    currency: str
    core: bool
    technical: dict[str, object] | None
    valuation: str
    regime: str
    confidence: str
    hard_gates_passed: bool
    rationale: str


def _rationale(symbol: str, technical: dict[str, object] | None) -> str:
    if technical is None:
        return f"{symbol}: no price data provided -- cannot compute a technical signal."
    history = "insufficient" if technical["ma_200w"] is None else "full"
    return (
        f"{symbol}: technical trend {technical['trend']!r}, stretch {technical['stretch']!r}, "
        f"from {history} weekly history. Fundamental valuation and regime assessment are not "
        "yet implemented (no data source configured) -- confidence is capped at 'insufficient' "
        "and hard_gates_passed is False until both layers exist."
    )


def assemble_candidates(prices_csv_path: str | Path) -> dict[str, Candidate]:
    """One Candidate per config/universe.yaml asset, keyed by symbol.

    Every configured universe asset gets an entry, whether or not the given
    CSV has price data for it -- missing price data is itself a fail-closed
    signal (technical=None), not silently skipped.
    """
    universe = {str(asset["symbol"]).upper(): asset for asset in load_universe()}
    prices = load_prices(prices_csv_path)
    candidates: dict[str, Candidate] = {}
    for symbol, asset in universe.items():
        values = prices.get(symbol)
        technical = asdict(calculate(values)) if values else None
        candidates[symbol] = Candidate(
            symbol=symbol,
            currency=str(asset["currency"]),
            core=bool(asset["core"]),
            technical=technical,
            valuation=NO_VALUATION_SOURCE,
            regime=NO_REGIME_SOURCE,
            confidence="insufficient",
            hard_gates_passed=False,
            rationale=_rationale(symbol, technical),
        )
    return candidates
