"""Yahoo Finance weekly-candle ingestion: fetch, validate, and snapshot -- nothing else.

Yahoo's chart endpoint is unofficial and undocumented -- no ToS support, no
SLA, and no guarantee it won't change or start rate-limiting without notice.
It is used here because it is, empirically, the only source found that
returns real multi-year weekly OHLC history for ASX-listed tickers without a
paid plan (see docs/wiki/ingestion.md). Like ingestion.finnhub, this module
produces validated, provenance-tagged weekly bars -- it does not compute
indicators, rank anything, or bear on any hard gate.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Callable

from ..snapshots import SnapshotStore
from .candles import WeeklyBar
from .data_sources import YahooConfig, load_yahoo_config
from .errors import (
    IngestionConfigError,
    IngestionRateLimitError,
    IngestionRequestError,
    IngestionResponseError,
)

Transport = Callable[[urllib.request.Request], bytes]

# A single-week move beyond this factor (either direction) is treated as
# corrupted provider data, not a real price -- discovered 2026-09-07: Yahoo's
# "IVV.AX" history repeatedly flip-flops ~15x between real ($120+) and bogus
# (~$8) values throughout 2010-2017, while every other tested ticker (VAS,
# VGS, NDQ, IZZ, VAE, BTC-USD) has none. The bound is set well above genuine
# extreme volatility (BTC's real -33% single-week COVID crash is a ratio of
# 0.665, comfortably inside it) so it only catches implausible data, never a
# real crash.
_MAX_WEEKLY_RATIO = 5.0
_MIN_WEEKLY_RATIO = 1 / _MAX_WEEKLY_RATIO


def _default_transport(request: urllib.request.Request, *, timeout: float) -> bytes:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise IngestionRateLimitError(f"Yahoo Finance rate limit hit (HTTP 429) requesting {request.full_url}") from exc
        raise IngestionRequestError(f"Yahoo Finance request failed: HTTP {exc.code} requesting {request.full_url}") from exc
    except urllib.error.URLError as exc:
        raise IngestionRequestError(f"Yahoo Finance request failed: {exc.reason}") from exc


def _parse_weekly_history(raw: bytes, *, symbol: str) -> list[WeeklyBar]:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestionResponseError(f"Yahoo Finance chart response for {symbol!r} was not valid JSON") from exc
    chart = data.get("chart") if isinstance(data, dict) else None
    if not isinstance(chart, dict):
        raise IngestionResponseError(f"Yahoo Finance chart response for {symbol!r} was not a JSON object")
    error = chart.get("error")
    if error:
        raise IngestionResponseError(f"Yahoo Finance returned an error for {symbol!r}: {error}")
    results = chart.get("result")
    if not results:
        raise IngestionResponseError(f"Yahoo Finance chart response for {symbol!r} has no result data")
    result = results[0]
    timestamps = result.get("timestamp")
    quote_list = result.get("indicators", {}).get("quote") or []
    closes = quote_list[0].get("close") if quote_list else None
    if not timestamps or not closes or len(timestamps) != len(closes):
        raise IngestionResponseError(f"Yahoo Finance chart response for {symbol!r} is missing timestamp/close data")
    bars = []
    for ts, close in zip(timestamps, closes):
        if close is None:
            # An in-progress current week (or a holiday gap) is not a real
            # closed bar -- dropping it, not substituting a guess.
            continue
        bar_date = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
        bars.append(WeeklyBar(date=bar_date, close=float(close)))
    if not bars:
        raise IngestionResponseError(f"Yahoo Finance chart response for {symbol!r} had no usable weekly bars")
    for previous, current in zip(bars, bars[1:]):
        ratio = current.close / previous.close
        if ratio > _MAX_WEEKLY_RATIO or ratio < _MIN_WEEKLY_RATIO:
            raise IngestionResponseError(
                f"Yahoo Finance chart response for {symbol!r} has an implausible week-over-week move "
                f"({previous.date}: {previous.close} -> {current.date}: {current.close}, ratio {ratio:.3f}) "
                "-- likely corrupted provider data; retry with a shorter --range that avoids the bad window"
            )
    return bars


def fetch_weekly_history(
    symbol: str,
    *,
    snapshot_store: SnapshotStore,
    range_: str = "20y",
    config: YahooConfig | None = None,
    transport: Transport | None = None,
) -> list[WeeklyBar]:
    """Fetch, snapshot, and validate weekly OHLC history for `symbol` (e.g. "IVV.AX").

    Fails closed (raises) on any transport/HTTP failure (rate limiting
    included) or a malformed/incomplete/error response. The raw response is
    snapshotted as soon as it's received -- before validation -- so evidence
    of a bad response is preserved even when this function goes on to raise.

    `range_` deliberately defaults to an explicit "20y", not Yahoo's own
    "max" range: empirically, "max" silently coarsens the response to
    monthly bars for a long-lived symbol despite interval=1wk being
    requested (confirmed 2026-09-07 -- every other explicit range up to
    "20y" returns genuine, gap-free 7-day-delta weekly bars for both
    ASX-listed ETFs and BTC-USD). Never request "max" here.
    """
    if not symbol or not symbol.strip():
        raise IngestionConfigError("symbol is required")
    config = config or load_yahoo_config()
    url = f"{config.base_url}/{symbol}?range={range_}&interval=1wk"
    request = urllib.request.Request(url, headers={"User-Agent": config.user_agent})
    active_transport = transport or (lambda req: _default_transport(req, timeout=config.timeout_seconds))
    raw = active_transport(request)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    snapshot_store.save(
        source=f"yahoo:chart:{symbol}",
        content=raw.decode("utf-8", errors="replace"),
        retrieved_at=retrieved_at,
        metadata={"provider": config.provider, "endpoint": "chart", "symbol": symbol, "range": range_, "interval": "1wk"},
    )
    return _parse_weekly_history(raw, symbol=symbol)
