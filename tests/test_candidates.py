from investment_system.candidates import NO_REGIME_SOURCE, NO_VALUATION_SOURCE, assemble_candidates
from investment_system.config import load_universe


def test_every_universe_asset_gets_a_candidate_even_with_no_price_data():
    # tests/fixtures/prices.csv only has a "TEST" asset -- no configured
    # universe symbol has price data in it, so every candidate should still
    # be present, just with technical=None.
    candidates = assemble_candidates("tests/fixtures/prices.csv")
    universe_symbols = {str(asset["symbol"]).upper() for asset in load_universe()}
    assert set(candidates) == universe_symbols
    for candidate in candidates.values():
        assert candidate.technical is None
        assert "no price data provided" in candidate.rationale


def test_confidence_and_hard_gates_are_insufficient_even_with_full_technical_history(tmp_path):
    # Regression test for the core design decision: even an asset with a
    # complete, high-quality technical signal must not be reported as
    # confident, because fundamental valuation and regime have no data
    # source at all yet -- 2 of the 3 required layers are structurally
    # absent, not merely uncertain.
    from datetime import date, timedelta

    csv_path = tmp_path / "ivv.csv"
    start = date(2020, 1, 6)
    rows = ["asset,date,close"]
    for i in range(210):
        rows.append(f"IVV,{(start + timedelta(weeks=i)).isoformat()},{100 + i}")
    csv_path.write_text("\n".join(rows) + "\n")

    candidates = assemble_candidates(csv_path)
    ivv = candidates["IVV"]
    assert ivv.technical is not None
    assert ivv.technical["ma_200w"] is not None  # full history really was available
    assert ivv.confidence == "insufficient"
    assert ivv.hard_gates_passed is False
    assert ivv.valuation == NO_VALUATION_SOURCE
    assert ivv.regime == NO_REGIME_SOURCE
    assert "not yet implemented" in ivv.rationale


def test_core_flag_is_read_from_universe_config():
    candidates = assemble_candidates("tests/fixtures/prices.csv")
    assert candidates["IVV"].core is True
    assert candidates["NDQ"].core is False
    assert candidates["CASH"].core is False
