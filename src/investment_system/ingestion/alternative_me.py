"""Alternative.me crypto Fear & Greed Index ingestion: fetch, validate, and
snapshot -- nothing else.

Alternative.me's `/fng/` endpoint is an official, documented, free API --
no key needed, no rate limit published as a hard block. This module produces
a single validated SentimentObservation; it does not compute indicators,
rank anything, or bear on any hard gate.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Callable

from ..snapshots import SnapshotStore
from .data_sources import AlternativeMeConfig, load_alternative_me_config
from .errors import (
    IngestionRateLimitError,
    IngestionRequestError,
    IngestionResponseError,
    IngestionStaleDataError,
)
from .sentiment import SentimentObservation

Transport = Callable[[urllib.request.Request], bytes]


def _default_transport(request: urllib.request.Request, *, timeout: float) -> bytes:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise IngestionRateLimitError(f"Alternative.me rate limit hit (HTTP 429) requesting {request.full_url}") from exc
        raise IngestionRequestError(f"Alternative.me request failed: HTTP {exc.code} requesting {request.full_url}") from exc
    except urllib.error.URLError as exc:
        raise IngestionRequestError(f"Alternative.me request failed: {exc.reason}") from exc


def _parse(raw: bytes, *, config: AlternativeMeConfig, retrieved_at: str, snapshot_id: str) -> SentimentObservation:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestionResponseError("Alternative.me fear & greed response was not valid JSON") from exc
    entries = data.get("data") if isinstance(data, dict) else None
    if not entries:
        raise IngestionResponseError("Alternative.me fear & greed response has no 'data' entries")
    entry = entries[0]
    try:
        value = float(entry["value"])
        category = str(entry["value_classification"])
        effective_at_dt = datetime.fromtimestamp(int(entry["timestamp"]), tz=timezone.utc)
    except (KeyError, TypeError, ValueError) as exc:
        raise IngestionResponseError("Alternative.me fear & greed response is missing/malformed fields") from exc
    age_seconds = (datetime.now(timezone.utc) - effective_at_dt).total_seconds()
    if age_seconds > config.max_age_seconds:
        raise IngestionStaleDataError(
            f"Alternative.me fear & greed observation is {age_seconds:.0f}s old "
            f"(max {config.max_age_seconds:.0f}s), effective_at={effective_at_dt.isoformat()}"
        )
    return SentimentObservation(
        value=value,
        category=category,
        provider=config.provider,
        effective_at=effective_at_dt.isoformat(),
        retrieved_at=retrieved_at,
        snapshot_id=snapshot_id,
    )


def fetch_crypto_fear_greed(
    *,
    snapshot_store: SnapshotStore,
    config: AlternativeMeConfig | None = None,
    transport: Transport | None = None,
) -> SentimentObservation:
    """Fetch, snapshot, and validate the latest crypto Fear & Greed reading.

    Fails closed (raises) on any transport/HTTP failure (rate limiting
    included), a malformed/incomplete response, or an observation older than
    `max_age_seconds`. The raw response is snapshotted as soon as it's
    received -- before validation -- so evidence of a bad response is
    preserved even when this function goes on to raise.
    """
    config = config or load_alternative_me_config()
    url = f"{config.base_url}/?limit=1&format=json"
    request = urllib.request.Request(url)
    active_transport = transport or (lambda req: _default_transport(req, timeout=config.timeout_seconds))
    raw = active_transport(request)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    snapshot = snapshot_store.save(
        source="alternative_me:fng",
        content=raw.decode("utf-8", errors="replace"),
        retrieved_at=retrieved_at,
        metadata={"provider": config.provider, "endpoint": "fng"},
    )
    return _parse(raw, config=config, retrieved_at=retrieved_at, snapshot_id=snapshot.snapshot_id)
