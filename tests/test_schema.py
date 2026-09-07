import json

from investment_system.engine import validate_report
from investment_system.schema import schema_errors


def _load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def test_example_practice_report_matches_the_schema():
    report = _load("reports/practice/P-001.example.json")
    assert schema_errors(report) == []


def test_example_practice_report_passes_business_rules_without_universe_check():
    report = _load("reports/practice/P-001.example.json")
    result = validate_report(report, check_universe_coverage=False)
    assert result.valid


def test_example_practice_report_is_incomplete_against_the_real_universe():
    # It's a single-asset illustrative fixture, not a full-universe live report.
    report = _load("reports/practice/P-001.example.json")
    result = validate_report(report)
    assert any(issue.code == "missing_assets" for issue in result.errors)


def test_schema_errors_reports_missing_required_field():
    report = _load("reports/practice/P-001.example.json")
    del report["quality_control"]
    errors = schema_errors(report)
    assert any("quality_control" in message for message in errors)


def test_schema_enforces_datetime_formats_and_btc_direction():
    report = _load("reports/practice/P-001.example.json")
    report["generated_at"] = "not-a-datetime"
    report["bitcoin"]["buy_assessment"]["decision"] = "SELL"
    errors = schema_errors(report)
    assert any("date-time" in message for message in errors)
    assert any("is not one of" in message for message in errors)


def test_practice_report_has_explicit_btc_and_sentiment_unavailability():
    report = _load("reports/practice/P-001.example.json")
    assert report["bitcoin"]["buy_assessment"]["decision"] == "INSUFFICIENT_DATA"
    assert report["sentiment"]["crypto_fear_greed"]["status"] == "unavailable"
    assert schema_errors(report) == []


def test_blake2b_gate_rejects_operator_thesis_as_an_unknown_field():
    # The operator_thesis/"stated belief" concept was deliberately removed
    # (2026-09-07) as irrelevant to the gate; this locks that removal in so
    # it can't quietly reappear as a schema drift.
    report = _load("reports/practice/P-001.example.json")
    report["bitcoin"]["blake2b_gate"]["operator_thesis"] = {"statement": "Anything."}
    errors = schema_errors(report)
    assert any("operator_thesis" in message for message in errors)
