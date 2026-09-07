import pytest

from investment_system.config import ModelConfig, BrokerageConfig
from investment_system.engine import calculate_signals, cost_table, load_prices


def test_fixture_loads_and_calculates():
    path = "tests/fixtures/prices.csv"
    assert len(load_prices(path)["TEST"]) == 21
    signal = calculate_signals(path)["TEST"]
    assert signal["ma_20w"] is not None
    assert signal["stretch"] in {"Normal", "Extended", "Extremely Extended"}


def test_duplicate_observation_is_rejected(tmp_path):
    csv_path = tmp_path / "dupes.csv"
    csv_path.write_text(
        "asset,date,close\n"
        "TEST,2020-01-03,100\n"
        "TEST,2020-01-03,101\n"
    )
    with pytest.raises(ValueError, match="duplicate observation"):
        load_prices(csv_path)


def test_cost_table_honours_config():
    config = ModelConfig(
        model_version="test",
        cash_yield_pct=5.0,
        brokerage=BrokerageConfig(minimum_aud=5.0, rate_pct=0.20, qualifying_buy_limit_aud=500.0),
    )
    table = {row["amount_aud"]: row for row in cost_table(config)}
    # 999 no longer qualifies for the free-buy treatment under this config's lower limit.
    assert table[999.0]["brokerage_aud"] == max(5.0, 999.0 * 0.20 / 100)
    assert table[2000.0]["brokerage_aud"] == max(5.0, 2000.0 * 0.20 / 100)


def test_cost_table_default_matches_committed_config():
    table = {row["amount_aud"]: row for row in cost_table()}
    assert table[999.0]["brokerage_aud"] == 0.0
    assert table[2000.0]["brokerage_aud"] == 11.0


def test_technical_signals_treat_every_asset_symbol_identically(tmp_path):
    # calculate_signals() is symbol-agnostic: it has no universe.yaml lookup,
    # no allowlist, no special-casing for BTC or any other asset. An asset
    # that isn't (and, per the design doc's BLAKE2b gate, currently cannot be)
    # in the tradable universe still gets the exact same deterministic
    # technical-signal computation as one that is — same fields, same
    # formulas, no different code path.
    csv_path = tmp_path / "prices.csv"
    rows = ["asset,date,close"]
    for i in range(21):
        date = f"2020-{1 + i // 4:02d}-{1 + (i % 4) * 7:02d}"
        rows.append(f"BTC,{date},{100 + i}")
        rows.append(f"NOT_IN_UNIVERSE,{date},{100 + i}")
    csv_path.write_text("\n".join(rows) + "\n")
    signals = calculate_signals(csv_path)
    btc, other = signals["BTC"], signals["NOT_IN_UNIVERSE"]
    assert set(btc.keys()) == set(other.keys())
    assert {k: v for k, v in btc.items() if k != "close"} == {k: v for k, v in other.items() if k != "close"}
