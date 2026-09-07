# Indicators reference

Implemented in [`src/investment_system/indicators.py`](../../src/investment_system/indicators.py).
All inputs are weekly closing prices, oldest first. Everything below is computed
purely from the `values: list[float]` passed to `calculate()` — no external data.

## Moving averages (`sma`)

Simple moving average over the last `period` values. Returns `None` (never an
approximation) if fewer than `period` values are available — this is the "missing
200W history must be reported as missing" rule from the design doc.

## MACD (`ema`, `macd_line`/`macd_signal`/`macd_histogram`)

- EMA seed = simple average of the first `period` values; standard EMA recursion
  from there. Requires `period` values, else `None`.
- MACD line = EMA(12) − EMA(26), first available once ≥26 values exist.
- Signal = EMA(9) of the MACD-line history, so it needs ≥26 + 9 − 1 = 34 values
  before it stops being `None` (it's legitimately `None`, not a bug, for 26–33
  values — the line exists before the signal does).
- Histogram = line − signal.

## RSI (`rsi`, default period 14)

**This is Wilder's smoothed RSI** — the definition quoted by brokers and virtually
every charting platform (TradingView, StockCharts, etc.), confirmed against
Wikipedia's "Relative strength index" article and macroption.com/rsi-calculation
(both state the identical recurrence). It is *not* the same as a plain trailing
average of the last `period` changes (sometimes called Cutler's RSI, which this
codebase used before 2026-09-04 — see [Changelog](changelog.md)):

```text
avg_gain (seed) = mean(first `period` gains)     avg_loss (seed) = mean(first `period` losses)
avg_gain = (avg_gain * (period - 1) + gain) / period   # repeated for every later change
avg_loss = (avg_loss * (period - 1) + loss) / period
RSI = 100 - 100 / (1 + avg_gain / avg_loss)
```

Because of that recurrence, **the result depends on the entire price history**,
not just the trailing window — unlike a plain moving average, you can't get the
same answer by only keeping the last `period + 1` prices. It's also
order-dependent: reordering older changes changes the answer, even though the
final window of raw prices is unchanged. Requires `period + 1` values, else
`None`. All-losses → `0.0`; no-change series → `50.0`. See
`tests/test_indicators.py::test_rsi_matches_wilders_smoothing_formula` for a
fully hand-traced worked example (period=5) verifying the exact recurrence,
independent of the implementation.

## Distances and drawdown

```text
distance_from_ma_pct = (close / ma - 1) * 100     # per MA, None if the MA is None
drawdown_from_ath_pct = (close / ath - 1) * 100   # ath = max(values), so this is <= 0
```

## Stretch label (from `distance_20w_pct`, i.e. `d20`)

| Condition | Label |
|---|---|
| `ma_20w` unavailable | `Insufficient Data` |
| `d20 >= 20` | `Extremely Extended` |
| `d20 >= 8` | `Extended` |
| `d20 <= -20` | `Deeply Oversold` |
| `d20 <= -8` | `Oversold` |
| otherwise | `Normal` |

These thresholds are an unvalidated first pass (the design doc explicitly says
thresholds aren't finalized) — expect them to move once real calibration happens.

## MA slope (`slope`, `slope_50w` / `slope_200w`)

Compares the current `period`-week SMA to the same SMA computed `SLOPE_LOOKBACK_WEEKS`
(currently **4**) weeks earlier. Returns `"Rising"` / `"Falling"` / `"Flat"`, or `None`
if either SMA can't be computed — which means **a slope needs `period + 4` values**,
4 more than the MA itself needs (e.g. `ma_50w` can exist with 50 values, but
`slope_50w` stays `None` until 54).

## Trend label (`_classify_trend`)

Uses `close` vs `ma_50w`, `ma_50w` vs `ma_200w` (golden/death cross), and
`slope_50w`. `slope_200w` is computed and reported but does not currently gate the
trend label itself.

| `close` vs `ma_50w` | `ma_50w` vs `ma_200w` | `slope_50w` | Label |
|---|---|---|---|
| — | — | — | `Insufficient Data` if `ma_50w` is `None` |
| above | below (death cross) | any | `Mixed` |
| above | above/unknown | `Rising` | `Strong Uptrend` |
| above | above/unknown | not `Rising` | `Uptrend` |
| below/equal | above (golden cross) | any | `Mixed` |
| below/equal | below/unknown | `Falling` | `Strong Downtrend` |
| below/equal | below/unknown | not `Falling` | `Downtrend` |

`Mixed` covers exactly the two cases where short-term price action and long-term
MA structure disagree: price has reclaimed the 50W average while the 200W average
is still the higher one, or price has lost the 50W average while the 200W average
is still the lower one. This produces the `Mixed` label required by the design doc
(the original implementation could never emit it — see
[Changelog](changelog.md#2026-09-04)).

## Worked example (from `tests/test_indicators.py`)

```python
calculate([100 + i for i in range(210)]).trend    # "Strong Uptrend"
calculate([400 - i for i in range(210)]).trend    # "Strong Downtrend"
# long decline then a sharp bounce -> close above ma_50w, but ma_50w still below ma_200w:
calculate([400 - i for i in range(209)] + [252]).trend  # "Mixed"
```
