from investment_system.validation import require_valid, validate_prices, validate_report


def test_validation_rejects_bad_prices_and_duplicates():
    result = validate_prices([
        {"asset": "TEST", "date": "2026-01-02", "close": "100"},
        {"asset": "TEST", "date": "2026-01-02", "close": "101"},
        {"asset": "TEST", "date": "2026-01-09", "close": "nan"},
        {"asset": "TEST", "date": "2026-01-16", "close": "-1"},
    ])
    assert not result.valid
    assert {issue.code for issue in result.errors} == {"duplicate_observation", "invalid_price"}


def test_validation_can_check_expected_assets():
    result = validate_prices(
        [{"asset": "IVV", "date": "2026-01-02", "close": "100"}],
        expected_assets={"IVV", "VAS"},
    )
    assert any(issue.code == "missing_assets" for issue in result.errors)


def test_require_valid_raises_only_on_errors():
    result = validate_prices([
        {"asset": "TEST", "date": "2026-01-09", "close": "100"},
        {"asset": "TEST", "date": "2026-01-02", "close": "101"},
    ])
    assert result.valid
    assert result.warnings
    require_valid(result)


def test_report_rejects_unavailable_sections_without_reasons():
    from investment_system.validation import validate_report

    report = {
        "report_kind": "practice",
        "report_id": "P-001",
        "decision_date": "2026-09-04",
        "rankings": [],
        "bitcoin": {"blake2b_gate": {"status": "unavailable"}},
        "sentiment": {
            "equity_fear_greed": {"status": "unavailable"},
            "crypto_fear_greed": {"status": "unavailable"},
        },
    }
    result = validate_report(report, expected_assets=None)
    assert {issue.code for issue in result.errors} >= {"missing_blake2b_reason", "missing_sentiment_reason"}


def test_report_validation_does_not_crash_on_malformed_rankings():
    from investment_system.validation import validate_report

    result = validate_report({"rankings": {"bad": "shape"}}, expected_assets=None)
    assert any(issue.code == "invalid_rankings" for issue in result.errors)


def _report(**overrides):
    base = {
        "report_kind": "practice",
        "report_id": "P-001",
        "decision_date": "2026-09-04",
        "rankings": [
            {"rank": 1, "asset": "IVV"},
            {"rank": 2, "asset": "CASH"},
        ],
    }
    base.update(overrides)
    return base


def test_report_rank_and_asset_rules_pass_for_a_well_formed_report():
    result = validate_report(_report(), expected_assets={"IVV", "CASH"})
    assert result.valid


def test_report_rejects_duplicate_ranks():
    result = validate_report(_report(rankings=[{"rank": 1, "asset": "IVV"}, {"rank": 1, "asset": "CASH"}]))
    assert {issue.code for issue in result.errors} == {"duplicate_rank"}


def test_report_rejects_non_contiguous_ranks():
    result = validate_report(_report(rankings=[{"rank": 1, "asset": "IVV"}, {"rank": 3, "asset": "CASH"}]))
    assert {issue.code for issue in result.errors} == {"non_contiguous_rank"}


def test_report_rejects_incomplete_universe_coverage():
    result = validate_report(_report(), expected_assets={"IVV", "CASH", "VAS"})
    assert any(issue.code == "missing_assets" for issue in result.errors)


def test_practice_report_id_must_match_kind():
    result = validate_report(_report(report_id="001"))
    assert any(issue.code == "report_id_kind_mismatch" for issue in result.errors)


def test_live_report_requires_a_monday():
    live = _report(report_kind="live", report_id="001", decision_date="2026-09-08")  # a Tuesday
    result = validate_report(live)
    assert any(issue.code == "live_report_not_monday" for issue in result.errors)

    live_on_monday = _report(report_kind="live", report_id="001", decision_date="2026-09-07")  # a Monday
    result = validate_report(live_on_monday)
    assert not any(issue.code == "live_report_not_monday" for issue in result.errors)


def test_practice_report_is_not_bound_by_the_monday_rule():
    result = validate_report(_report(decision_date="2026-09-08"))  # a Tuesday, but this is a practice report
    assert not any(issue.code == "live_report_not_monday" for issue in result.errors)
