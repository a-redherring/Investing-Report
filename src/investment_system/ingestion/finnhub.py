"""Finnhub quote ingestion: fetch, validate, and snapshot -- nothing else.

This module produces a single validated FinnhubQuote per call. It does not
compute indicators, rank anything, or bear on any hard gate (BTCB2's
blake2b_gate included). Historical/weekly-candle ingestion (needed to feed
indicators.calculate()) is not implemented here yet -- see docs/wiki/ingestion.md.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from ..snapshots import SnapshotStore
from .data_sources import FinnhubConfig, load_finnhub_config
from .errors import (
    IngestionConfigError,
    IngestionRateLimitError,
    IngestionRequestError,
    IngestionResponseError,
    IngestionStaleDataError,
)

Transport = Callable[[urllib.request.Request], bytes]

_REQUIRED_QUOTE_FIELDS = ("c", "h", "l", "o", "pc", "t")


@dataclass(frozen=True)
class FinnhubQuote:
    symbol: str
    current: float
    high: float
    low: float
    open: float
    previous_close: float
    quoted_at: str  # ISO 8601 UTC, derived from Finnhub's `t` (unix seconds)
    retrieved_at: str
    snapshot_id: str


def _default_transport(request: urllib.request.Request, *, timeout: float) -> bytes:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise IngestionRateLimitError(f"Finnhub rate limit hit (HTTP 429) requesting {request.full_url}") from exc
        raise IngestionRequestError(f"Finnhub request failed: HTTP {exc.code} requesting {request.full_url}") from exc
    except urllib.error.URLError as exc:
        raise IngestionRequestError(f"Finnhub request failed: {exc.reason}") from exc


def _build_request(config: FinnhubConfig, endpoint: str, params: dict[str, str], api_key: str) -> urllib.request.Request:
    query = urllib.parse.urlencode(params)
    url = f"{config.base_url}/{endpoint}?{query}"
    # The API key is a header, never part of the URL/query string, so it can
    # never end up in a logged URL, proxy log, browser history, or this
    # snapshot's own metadata.
    return urllib.request.Request(url, headers={"X-Finnhub-Token": api_key})


def _parse_quote(raw: bytes, *, symbol: str) -> dict[str, float]:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestionResponseError(f"Finnhub quote response for {symbol!r} was not valid JSON") from exc
    if not isinstance(data, dict):
        raise IngestionResponseError(f"Finnhub quote response for {symbol!r} was not a JSON object")
    missing = [field for field in _REQUIRED_QUOTE_FIELDS if field not in data]
    if missing:
        raise IngestionResponseError(f"Finnhub quote response for {symbol!r} is missing fields: {missing}")
    try:
        parsed = {field: float(data[field]) for field in _REQUIRED_QUOTE_FIELDS}
    except (TypeError, ValueError) as exc:
        raise IngestionResponseError(f"Finnhub quote response for {symbol!r} has non-numeric fields") from exc
    if parsed["t"] == 0 and parsed["c"] == 0:
        # Finnhub returns HTTP 200 with every field zeroed for a symbol it
        # doesn't recognize, rather than a 4xx -- this is the documented
        # signal for "no data", and must not be read as a real zero price.
        raise IngestionResponseError(f"Finnhub returned no data for symbol {symbol!r} (unrecognized symbol or unsupported market)")
    return parsed


def fetch_quote(
    symbol: str,
    *,
    snapshot_store: SnapshotStore,
    api_key: str | None = None,
    config: FinnhubConfig | None = None,
    transport: Transport | None = None,
) -> FinnhubQuote:
    """Fetch, snapshot, and validate a Finnhub quote for `symbol`.

    Fails closed (raises) on: a missing API key, any transport/HTTP failure
    (rate limiting included), a malformed/incomplete/unrecognized-symbol
    response, or a quote older than the configured max age. The raw response
    is snapshotted as soon as it's received -- before validation -- so
    evidence of a bad response is preserved even when this function goes on
    to raise.
    """
    if not symbol or not symbol.strip():
        raise IngestionConfigError("symbol is required")
    config = config or load_finnhub_config()
    key = api_key or os.environ.get(config.api_key_env_var)
    if not key:
        raise IngestionConfigError(f"{config.api_key_env_var} is not set in the environment")
    request = _build_request(config, "quote", {"symbol": symbol}, key)
    active_transport = transport or (lambda req: _default_transport(req, timeout=config.timeout_seconds))
    raw = active_transport(request)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    snapshot = snapshot_store.save(
        source=f"finnhub:quote:{symbol}",
        content=raw.decode("utf-8", errors="replace"),
        retrieved_at=retrieved_at,
        metadata={"provider": config.provider, "endpoint": "quote", "symbol": symbol},
    )
    parsed = _parse_quote(raw, symbol=symbol)
    quoted_at = datetime.fromtimestamp(parsed["t"], tz=timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - quoted_at).total_seconds()
    if age_seconds > config.max_quote_age_seconds:
        raise IngestionStaleDataError(
            f"Finnhub quote for {symbol!r} is {age_seconds:.0f}s old "
            f"(max {config.max_quote_age_seconds:.0f}s), quoted_at={quoted_at.isoformat()}"
        )
    return FinnhubQuote(
        symbol=symbol,
        current=parsed["c"],
        high=parsed["h"],
        low=parsed["l"],
        open=parsed["o"],
        previous_close=parsed["pc"],
        quoted_at=quoted_at.isoformat(),
        retrieved_at=retrieved_at,
        snapshot_id=snapshot.snapshot_id,
    )
