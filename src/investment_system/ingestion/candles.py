"""Shared weekly-price-bar contract every historical ingestion adapter produces.

Decouples engine.load_prices()'s asset,date,close CSV contract from any one
provider's response shape, so downstream code never needs to know which
provider produced a given bar.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeeklyBar:
    date: str  # ISO 8601 date (YYYY-MM-DD)
    close: float
