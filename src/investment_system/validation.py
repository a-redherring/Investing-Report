"""Fail-closed validation for input snapshots and report prerequisites."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class ValidationResult:
    issues: tuple[ValidationIssue, ...]

    @property
    def valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "error")

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")


def validate_prices(rows: Iterable[dict[str, str]], expected_assets: set[str] | None = None) -> ValidationResult:
    """Validate raw CSV rows without changing or sorting them."""
    issues: list[ValidationIssue] = []
    seen: set[tuple[str, str]] = set()
    assets: set[str] = set()
    previous_dates: dict[str, date] = {}
    for index, row in enumerate(rows, start=2):
        asset = row.get("asset", "").strip().upper()
        raw_date = row.get("date", "").strip()
        raw_close = row.get("close", "").strip()
        if not asset or not raw_date or not raw_close:
            issues.append(ValidationIssue("missing_field", f"row {index} requires asset, date, and close"))
            continue
        assets.add(asset)
        try:
            observation_date = date.fromisoformat(raw_date)
        except ValueError:
            issues.append(ValidationIssue("invalid_date", f"row {index} has invalid ISO date {raw_date!r}"))
            continue
        key = (asset, raw_date)
        if key in seen:
            issues.append(ValidationIssue("duplicate_observation", f"duplicate observation for {asset} on {raw_date}"))
        seen.add(key)
        try:
            close = float(raw_close)
        except ValueError:
            issues.append(ValidationIssue("invalid_price", f"row {index} has non-numeric close {raw_close!r}"))
            continue
        if not math.isfinite(close) or close <= 0:
            issues.append(ValidationIssue("invalid_price", f"row {index} close must be finite and > 0"))
        prior = previous_dates.get(asset)
        if prior is not None and observation_date <= prior:
            issues.append(ValidationIssue("unsorted_dates", f"{asset} dates must be strictly increasing in source order", "warning"))
        previous_dates[asset] = observation_date
    if expected_assets:
        missing = sorted(expected_assets - assets)
        if missing:
            issues.append(ValidationIssue("missing_assets", f"missing expected assets: {', '.join(missing)}"))
    return ValidationResult(tuple(issues))


def validate_report(report: dict[str, object], *, expected_assets: set[str] | None = None) -> ValidationResult:
    """Validate cross-field report rules the JSON Schema cannot express on its own.

    The schema in schemas/frozen-report.schema.json enforces per-field shape
    (e.g. report_id matches P-### or ###) but not relationships between fields
    such as which pattern applies for a given report_kind, or properties of the
    rankings list as a whole. This checks those relationships; keep the schema
    as the structural contract and this as the business-rule layer on top of it.
    """
    issues: list[ValidationIssue] = []
    report_kind = report.get("report_kind")
    report_id = str(report.get("report_id", ""))
    decision_date_raw = report.get("decision_date")
    rankings_value = report.get("rankings")
    rankings = rankings_value if isinstance(rankings_value, list) else []
    if rankings_value is not None and not isinstance(rankings_value, list):
        issues.append(ValidationIssue("invalid_rankings", "rankings must be an array"))

    if report_kind == "practice" and not re.fullmatch(r"P-\d{3}", report_id):
        issues.append(ValidationIssue("report_id_kind_mismatch", f"practice report_id must match P-###, got {report_id!r}"))
    elif report_kind == "live" and not re.fullmatch(r"\d{3}", report_id):
        issues.append(ValidationIssue("report_id_kind_mismatch", f"live report_id must match ###, got {report_id!r}"))

    if report_kind == "live" and isinstance(decision_date_raw, str):
        try:
            if date.fromisoformat(decision_date_raw).weekday() != 0:
                issues.append(ValidationIssue("live_report_not_monday", f"live report decision_date {decision_date_raw} is not a Monday"))
        except ValueError:
            issues.append(ValidationIssue("invalid_date", f"decision_date {decision_date_raw!r} is not a valid ISO date"))

    ranking_objects = [entry for entry in rankings if isinstance(entry, dict)]
    if len(ranking_objects) != len(rankings):
        issues.append(ValidationIssue("invalid_ranking_entry", "every ranking entry must be an object"))
    ranks = [entry.get("rank") for entry in ranking_objects]
    if any(not isinstance(rank, int) or isinstance(rank, bool) for rank in ranks):
        issues.append(ValidationIssue("invalid_rank", "every ranking entry requires an integer rank"))
    elif len(set(ranks)) != len(ranks):
        issues.append(ValidationIssue("duplicate_rank", "ranks must be unique"))
    elif ranks and sorted(ranks) != list(range(1, len(ranks) + 1)):
        issues.append(ValidationIssue("non_contiguous_rank", "ranks must be contiguous starting at 1"))

    if expected_assets:
        assets = {str(entry.get("asset", "")).strip().upper() for entry in ranking_objects}
        missing = sorted(expected_assets - assets)
        if missing:
            issues.append(ValidationIssue("missing_assets", f"missing expected assets: {', '.join(missing)}"))

    btc = report.get("bitcoin")
    if isinstance(btc, dict):
        for name in ("buy_assessment", "sell_assessment"):
            assessment = btc.get(name)
            if isinstance(assessment, dict) and assessment.get("decision") == "INSUFFICIENT_DATA" and not assessment.get("rationale"):
                issues.append(ValidationIssue("missing_btc_rationale", f"bitcoin.{name} requires rationale when insufficient"))
        gate = btc.get("blake2b_gate")
        if isinstance(gate, dict) and gate.get("status") == "unavailable" and not gate.get("reason"):
            issues.append(ValidationIssue("missing_blake2b_reason", "bitcoin.blake2b_gate requires reason when unavailable"))

    sentiment = report.get("sentiment")
    if isinstance(sentiment, dict):
        for name in ("equity_fear_greed", "crypto_fear_greed"):
            observation = sentiment.get(name)
            if isinstance(observation, dict):
                status = observation.get("status")
                if status == "unavailable" and not observation.get("reason"):
                    issues.append(ValidationIssue("missing_sentiment_reason", f"sentiment.{name} requires reason when unavailable"))
                if status == "observed" and (observation.get("value") is None or not observation.get("provider") or not observation.get("effective_at") or not observation.get("retrieved_at")):
                    issues.append(ValidationIssue("incomplete_sentiment_observation", f"sentiment.{name} observed status requires value, provider, effective_at, and retrieved_at"))

    return ValidationResult(tuple(issues))


def require_valid(result: ValidationResult) -> None:
    """Raise a concise error when a validation result contains errors."""
    if not result.valid:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in result.errors)
        raise ValueError(details)
