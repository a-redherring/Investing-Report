import pytest

from investment_system.costs import asx_brokerage, brokerage_drag
from investment_system.indicators import calculate, rsi


def test_moving_average_and_ath():
    snapshot = calculate(list(range(1, 21)))
    assert snapshot.ma_20w == 10.5
    assert snapshot.ath == 20
    assert snapshot.drawdown_from_ath_pct == 0


def test_missing_long_history_is_explicit():
    snapshot = calculate(list(range(1, 21)))
    assert snapshot.ma_50w is None
    assert snapshot.trend == "Insufficient Data"


def test_fee_schedule():
    assert asx_brokerage(999, qualifying_buy=True) == 0
    assert asx_brokerage(2000) == 11
    assert round(brokerage_drag(2000), 3) == 0.55


def test_stretch_boundaries():
    assert calculate([100] * 19 + [112]).stretch == "Extended"
    assert calculate([100] * 19 + [130]).stretch == "Extremely Extended"
    assert calculate([100] * 19 + [88]).stretch == "Oversold"
    assert calculate([100] * 19 + [70]).stretch == "Deeply Oversold"
    assert calculate([100] * 20).stretch == "Normal"


def test_rsi_edge_cases():
    assert rsi(list(range(1, 16))) == 100.0
    assert rsi(list(range(15, 0, -1))) == 0.0
    assert rsi([10.0] * 15) == 50.0
    assert rsi([1.0] * 10) is None


def test_rsi_matches_wilders_smoothing_formula():
    # Golden fixture, period=5. Prices rise by 2 for the first 5 weeks, drop by
    # 10 in week 6, then resume rising by 2. Wilder's formula
    # (Wikipedia "Relative strength index"; also stated identically by
    # macroption.com/rsi-calculation) is:
    #   avg_gain/avg_loss seed = simple average of the first `period` changes
    #   avg = (prev * (period - 1) + new) / period   thereafter
    # Hand-traced here (not derived from the implementation):
    #   changes:      +2  +2  +2  +2  +2 | -10  +2  +2  +2
    #   seed avg_gain = mean(2,2,2,2,2) = 2.0
    #   seed avg_loss = mean(0,0,0,0,0) = 0.0
    #   step (gain=0,  loss=10): avg_gain=(2.0*4+0)/5=1.6     avg_loss=(0.0*4+10)/5=2.0
    #   step (gain=2,  loss=0):  avg_gain=(1.6*4+2)/5=1.68    avg_loss=(2.0*4+0)/5=1.6
    #   step (gain=2,  loss=0):  avg_gain=(1.68*4+2)/5=1.744  avg_loss=(1.6*4+0)/5=1.28
    #   step (gain=2,  loss=0):  avg_gain=(1.744*4+2)/5=1.7952 avg_loss=(1.28*4+0)/5=1.024
    #   RS = 1.7952 / 1.024 = 1.753125
    #   RSI = 100 - 100 / (1 + 1.753125) = 63.677639046538026
    prices = [100, 102, 104, 106, 108, 110, 100, 102, 104, 106]
    assert rsi(prices, period=5) == pytest.approx(63.677639046538026)


def test_slope_requires_extra_lookback_history():
    snapshot = calculate(list(range(1, 51)))
    assert snapshot.ma_50w is not None
    assert snapshot.slope_50w is None


def test_strong_uptrend_and_downtrend():
    rising = calculate([100 + i for i in range(210)])
    assert rising.trend == "Strong Uptrend"
    assert rising.slope_50w == "Rising"
    assert rising.slope_200w == "Rising"

    falling = calculate([400 - i for i in range(210)])
    assert falling.trend == "Strong Downtrend"
    assert falling.slope_50w == "Falling"
    assert falling.slope_200w == "Falling"


def test_mixed_trend_when_price_and_long_term_structure_disagree():
    # Long decline, then a sharp bounce: close reclaims the 50W average, but the
    # 50W average is still below the 200W average (death cross intact).
    bounce = calculate([400 - i for i in range(209)] + [400 - 208 + 60])
    assert bounce.trend == "Mixed"

    # Long rise, then a sharp drop: close falls below the 50W average, but the
    # 50W average is still above the 200W average (golden cross intact).
    drop = calculate([100 + i for i in range(209)] + [100 + 208 - 60])
    assert drop.trend == "Mixed"
