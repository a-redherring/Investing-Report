from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from .config import ModelConfig, load_model_config, load_universe
from .costs import asx_brokerage
from .indicators import calculate
from .schema import schema_errors
from .validation import ValidationIssue, ValidationResult, require_valid, validate_prices
from .validation import validate_report as validate_report_rules
from .snapshots import SnapshotStore


def load_prices(path: str | Path) -> dict[str, list[float]]:
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    require_valid(validate_prices(rows))
    prices: dict[str, dict[str, float]] = defaultdict(dict)
    for row in rows:
        asset, obs_date = row["asset"].strip().upper(), row["date"].strip()
        prices[asset][obs_date] = float(row["close"])
    return {asset: [rows[d] for d in sorted(rows)] for asset, rows in prices.items()}


def calculate_signals(path: str | Path) -> dict[str, dict[str, object]]:
    return {asset: asdict(calculate(values)) for asset, values in load_prices(path).items()}


def cost_table(config: ModelConfig | None = None) -> list[dict[str, float]]:
    brokerage = (config or load_model_config()).brokerage
    rows = []
    for amount in (999.0, 2000.0, 4000.0):
        qualifying_buy = amount <= brokerage.qualifying_buy_limit_aud
        fee = asx_brokerage(amount, qualifying_buy=qualifying_buy, minimum=brokerage.minimum_aud, rate_pct=brokerage.rate_pct)
        rows.append({"amount_aud": amount, "brokerage_aud": fee, "drag_pct": fee / amount * 100})
    return rows


def config_snapshot() -> dict[str, object]:
    return {"model": asdict(load_model_config()), "universe": load_universe()}


def validate_report(report: dict[str, object], *, check_universe_coverage: bool = True, snapshot_db: str | Path | None = None) -> ValidationResult:
    """Validate a report against both the JSON Schema and the cross-field business rules.

    The schema (schemas/frozen-report.schema.json) is the structural contract;
    this adds the relationships it cannot express (rank/id/date rules) and, by
    default, checks that every configured universe asset is ranked.
    """
    issues = [ValidationIssue("schema", message) for message in schema_errors(report)]
    expected = {str(asset["symbol"]).upper() for asset in load_universe()} if check_universe_coverage else None
    issues.extend(validate_report_rules(report, expected_assets=expected).issues)
    if snapshot_db is not None:
        snapshot_id = report.get("input_snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            issues.append(ValidationIssue("missing_snapshot_reference", "input_snapshot_id is required when snapshot verification is enabled"))
        else:
            try:
                with SnapshotStore(snapshot_db) as store:
                    store.get(snapshot_id)
            except KeyError:
                issues.append(ValidationIssue("unknown_snapshot_reference", f"input_snapshot_id {snapshot_id!r} is not present in the snapshot store"))
    return ValidationResult(tuple(issues))
