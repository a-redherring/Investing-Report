"""CNN equity Fear & Greed Index ingestion: fetch, validate, and snapshot --
nothing else.

CNN's chart-data endpoint is unofficial and undocumented -- no ToS support,
no SLA, and it actively blocks requests lacking browser-like headers (a
plain request with no Referer returns "I'm a teapot. You're a bot."; a
User-Agent plus a Referer matching the real page is enough to pass,
confirmed 2026-09-07). Used because it's the same index the report schema's
equity_fear_greed field was named after, and no official free alternative
was found. This module produces a single validated SentimentObservation; it
does not compute indicators, rank anything, or bear on any hard gate.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Callable

from ..snapshots import SnapshotStore
from .data_sources import CnnFearGreedConfig, load_cnn_fear_greed_config
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
            raise IngestionRateLimitError(f"CNN rate limit hit (HTTP 429) requesting {request.full_url}") from exc
        raise IngestionRequestError(f"CNN request failed: HTTP {exc.code} requesting {request.full_url}") from exc
    except urllib.error.URLError as exc:
        raise IngestionRequestError(f"CNN request failed: {exc.reason}") from exc


def _parse(raw: bytes, *, config: CnnFearGreedConfig, retrieved_at: str, snapshot_id: str) -> SentimentObservation:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestionResponseError("CNN fear & greed response was not valid JSON -- likely blocked as a bot") from exc
    fear_and_greed = data.get("fear_and_greed") if isinstance(data, dict) else None
    if not isinstance(fear_and_greed, dict):
        raise IngestionResponseError("CNN fear & greed response is missing 'fear_and_greed'")
    try:
        value = float(fear_and_greed["score"])
        category = str(fear_and_greed["rating"])
        effective_at_dt = datetime.fromisoformat(str(fear_and_greed["timestamp"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise IngestionResponseError("CNN fear & greed response is missing/malformed fields") from exc
    if effective_at_dt.tzinfo is None:
        effective_at_dt = effective_at_dt.replace(tzinfo=timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - effective_at_dt).total_seconds()
    if age_seconds > config.max_age_seconds:
        raise IngestionStaleDataError(
            f"CNN fear & greed observation is {age_seconds:.0f}s old "
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


def fetch_equity_fear_greed(
    *,
    snapshot_store: SnapshotStore,
    config: CnnFearGreedConfig | None = None,
    transport: Transport | None = None,
) -> SentimentObservation:
    """Fetch, snapshot, and validate the latest equity Fear & Greed reading.

    Fails closed (raises) on any transport/HTTP failure (rate limiting and
    bot-blocking included), a malformed/incomplete response, or an
    observation older than `max_age_seconds`. The raw response is
    snapshotted as soon as it's received -- before validation -- so evidence
    of a bad response is preserved even when this function goes on to raise.
    """
    config = config or load_cnn_fear_greed_config()
    request = urllib.request.Request(config.base_url, headers={"User-Agent": config.user_agent, "Referer": config.referer, "Accept": "application/json"})
    active_transport = transport or (lambda req: _default_transport(req, timeout=config.timeout_seconds))
    raw = active_transport(request)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    snapshot = snapshot_store.save(
        source="cnn:fear_and_greed",
        content=raw.decode("utf-8", errors="replace"),
        retrieved_at=retrieved_at,
        metadata={"provider": config.provider, "endpoint": "fearandgreed/graphdata"},
    )
    return _parse(raw, config=config, retrieved_at=retrieved_at, snapshot_id=snapshot.snapshot_id)
