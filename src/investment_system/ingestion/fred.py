"""FRED (Federal Reserve Bank of St. Louis) macro-indicator ingestion: fetch,
validate, and snapshot the latest observation of a single named economic
data series -- nothing else.

FRED is an official, free, documented API (a signup-required key, same tier
as Alpha Vantage/CoinGecko's demo keys -- see docs/wiki/ingestion.md). This
module produces a single validated MacroObservation -- one raw number for
one FRED series -- for a human/AI's regime judgment to consume. It does
**not** classify a regime label (Deteriorating/Stable/Improving/Structural
Bull/Structural Breakout/Crisis/Unclear): synthesizing multiple indicators
into one of those labels is a judgment call this project's own design doc
treats as qualitative, not a formula this adapter should invent.

Unlike every other adapter here, FRED's API only accepts the key as a URL
query parameter -- there is no header-based alternative. `_default_transport`
therefore deliberately never includes the request URL in any error message
(unlike ingestion.finnhub/yahoo/cnn_fear_greed, where the URL contains no
secret and is safe to log) -- the key must never end up in an exception
message, log line, or anywhere else it could leak. It's also never part of
the snapshot's `source`/metadata, only the raw response body is stored.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date as _date, datetime, timezone
from typing import Callable

from ..snapshots import SnapshotStore
from .data_sources import FredConfig, load_fred_config
from .errors import (
    IngestionConfigError,
    IngestionRateLimitError,
    IngestionRequestError,
    IngestionResponseError,
    IngestionStaleDataError,
)

Transport = Callable[[urllib.request.Request], bytes]


@dataclass(frozen=True)
class MacroObservation:
    series_id: str
    value: float
    date: str  # ISO 8601 date of the observation itself
    provider: str
    retrieved_at: str
    snapshot_id: str


def _default_transport(request: urllib.request.Request, *, timeout: float) -> bytes:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise IngestionRateLimitError("FRED rate limit hit (HTTP 429)") from exc
        raise IngestionRequestError(f"FRED request failed: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise IngestionRequestError(f"FRED request failed: {exc.reason}") from exc


def _parse(raw: bytes, *, series_id: str, config: FredConfig, retrieved_at: str, snapshot_id: str) -> MacroObservation:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestionResponseError(f"FRED response for {series_id!r} was not valid JSON") from exc
    if isinstance(data, dict) and "error_message" in data:
        raise IngestionResponseError(f"FRED returned an error for {series_id!r}: {data['error_message']}")
    observations = data.get("observations") if isinstance(data, dict) else None
    if not observations:
        raise IngestionResponseError(f"FRED response for {series_id!r} has no observations")
    # Requested with sort_order=desc, so observations[0] is the newest. FRED
    # marks a missing/not-yet-published reading with the literal string "."
    # -- walk forward until the first real value, never treating "." as
    # zero or interpolating across it.
    latest = next((entry for entry in observations if entry.get("value") != "."), None)
    if latest is None:
        raise IngestionResponseError(f"FRED response for {series_id!r} has no non-missing observations in the requested window")
    try:
        value = float(latest["value"])
        observation_date = _date.fromisoformat(latest["date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise IngestionResponseError(f"FRED response for {series_id!r} has a malformed observation") from exc
    age_days = (datetime.now(timezone.utc).date() - observation_date).days
    if age_days > config.max_age_days:
        raise IngestionStaleDataError(
            f"FRED observation for {series_id!r} is {age_days}d old (max {config.max_age_days:.0f}d), date={observation_date.isoformat()}"
        )
    return MacroObservation(
        series_id=series_id,
        value=value,
        date=observation_date.isoformat(),
        provider=config.provider,
        retrieved_at=retrieved_at,
        snapshot_id=snapshot_id,
    )


def fetch_series_latest(
    series_id: str,
    *,
    snapshot_store: SnapshotStore,
    api_key: str | None = None,
    config: FredConfig | None = None,
    transport: Transport | None = None,
) -> MacroObservation:
    """Fetch, snapshot, and validate the latest real observation of `series_id` (e.g. "VIXCLS").

    Fails closed (raises) on a missing API key, any transport/HTTP failure
    (rate limiting included), a malformed/incomplete response, a window with
    no non-missing observation, or a latest value older than
    `max_age_days`. The raw response is snapshotted as soon as it's
    received -- before validation -- so evidence of a bad response is
    preserved even when this function goes on to raise.
    """
    if not series_id or not series_id.strip():
        raise IngestionConfigError("series_id is required")
    config = config or load_fred_config()
    key = api_key or os.environ.get(config.api_key_env_var)
    if not key:
        raise IngestionConfigError(f"{config.api_key_env_var} is not set in the environment")
    params = {"series_id": series_id, "api_key": key, "file_type": "json", "sort_order": "desc", "limit": "10"}
    url = f"{config.base_url}/series/observations?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url)
    active_transport = transport or (lambda req: _default_transport(req, timeout=config.timeout_seconds))
    raw = active_transport(request)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    snapshot = snapshot_store.save(
        source=f"fred:{series_id}",
        content=raw.decode("utf-8", errors="replace"),
        retrieved_at=retrieved_at,
        metadata={"provider": config.provider, "endpoint": "series/observations", "series_id": series_id},
    )
    return _parse(raw, series_id=series_id, config=config, retrieved_at=retrieved_at, snapshot_id=snapshot.snapshot_id)
