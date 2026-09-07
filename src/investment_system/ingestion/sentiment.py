"""Shared Fear & Greed observation contract every sentiment adapter produces.

Mirrors the report schema's sentimentObservation shape (see
schemas/frozen-report.schema.json) so a fetched observation can be embedded
into a report's sentiment.equity_fear_greed / sentiment.crypto_fear_greed
with status="observed" and no further translation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SentimentObservation:
    value: float  # 0-100
    category: str  # provider's own label, e.g. "Fear", "extreme greed" -- passed through as-is, not case-normalized
    provider: str
    effective_at: str  # ISO 8601 datetime
    retrieved_at: str  # ISO 8601 datetime
    snapshot_id: str
