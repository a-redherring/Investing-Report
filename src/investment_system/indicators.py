from __future__ import annotations

from dataclasses import dataclass

SLOPE_LOOKBACK_WEEKS = 4


def sma(values: list[float], period: int) -> float | None:
    return sum(values[-period:]) / period if len(values) >= period else None


def slope(values: list[float], period: int, lookback: int = SLOPE_LOOKBACK_WEEKS) -> str | None:
    current = sma(values, period)
    prior = sma(values[:-lookback], period) if lookback else current
    if current is None or prior is None:
        return None
    return "Rising" if current > prior else "Falling" if current < prior else "Flat"


def rsi(values: list[float], period: int = 14) -> float | None:
    # Wilder's smoothed RSI (the definition quoted by brokers and most charting
    # platforms), not Cutler's plain trailing-window average: the first
    # `period` gains/losses seed a simple average, then every later change is
    # folded in via newval = (prevval * (period - 1) + newdata) / period. This
    # makes the result depend on the full history, not just the trailing
    # window, and order-dependent (unlike Cutler's). See docs/wiki/indicators.md.
    if len(values) < period + 1:
        return None
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
    if avg_loss == 0:
        return 100.0 if avg_gain else 50.0
    return 100 - 100 / (1 + avg_gain / avg_loss)


def ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    result = sum(values[:period]) / period
    multiplier = 2 / (period + 1)
    for value in values[period:]:
        result = (value - result) * multiplier + result
    return result


@dataclass(frozen=True)
class TechnicalSnapshot:
    close: float
    ma_20w: float | None
    ma_50w: float | None
    ma_200w: float | None
    rsi_weekly: float | None
    macd_line: float | None
    macd_signal: float | None
    macd_histogram: float | None
    ath: float
    drawdown_from_ath_pct: float
    distances_pct: dict[str, float | None]
    slope_50w: str | None
    slope_200w: str | None
    stretch: str
    trend: str


def _classify_trend(close: float, ma50: float | None, ma200: float | None, slope_50w: str | None) -> str:
    if ma50 is None:
        return "Insufficient Data"
    above_50w = close > ma50
    golden_cross = ma200 is not None and ma50 > ma200
    death_cross = ma200 is not None and ma50 < ma200
    rising_50w = slope_50w == "Rising"
    falling_50w = slope_50w == "Falling"
    if above_50w:
        if death_cross:
            return "Mixed"
        if rising_50w and (ma200 is None or golden_cross):
            return "Strong Uptrend"
        return "Uptrend"
    if golden_cross:
        return "Mixed"
    if falling_50w and (ma200 is None or death_cross):
        return "Strong Downtrend"
    return "Downtrend"


def calculate(values: list[float], rsi_period: int = 14) -> TechnicalSnapshot:
    if not values:
        raise ValueError("at least one price is required")
    close, ath = values[-1], max(values)
    ma20, ma50, ma200 = (sma(values, p) for p in (20, 50, 200))
    macd = None
    signal = None
    if len(values) >= 26:
        fast = ema(values, 12)
        slow = ema(values, 26)
        macd = fast - slow if fast is not None and slow is not None else None
        macd_history = [ema(values[:i], 12) - ema(values[:i], 26) for i in range(26, len(values) + 1)]
        macd_history = [x for x in macd_history if x is not None]
        signal = ema(macd_history, 9)
    histogram = macd - signal if macd is not None and signal is not None else None
    distances = {f"{p}w": (close / ma - 1) * 100 if ma else None for p, ma in ((20, ma20), (50, ma50), (200, ma200))}
    d20 = distances["20w"]
    stretch = "Insufficient Data" if d20 is None else ("Extremely Extended" if d20 >= 20 else "Extended" if d20 >= 8 else "Deeply Oversold" if d20 <= -20 else "Oversold" if d20 <= -8 else "Normal")
    slope_50w = slope(values, 50)
    slope_200w = slope(values, 200)
    trend = _classify_trend(close, ma50, ma200, slope_50w)
    return TechnicalSnapshot(close, ma20, ma50, ma200, rsi(values, rsi_period), macd, signal, histogram, ath, (close / ath - 1) * 100, distances, slope_50w, slope_200w, stretch, trend)
