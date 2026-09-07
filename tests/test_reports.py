import json

import pytest

from investment_system.reports import freeze_report


def _report():
    with open("reports/practice/P-001.example.json", encoding="utf-8") as handle:
        return json.load(handle)


def test_freeze_requires_explicit_confirmation(tmp_path):
    with pytest.raises(ValueError, match="explicit confirmation"):
        freeze_report(_report(), tmp_path, check_universe_coverage=False)


def test_freeze_is_idempotent_but_rejects_changed_content(tmp_path):
    report = _report()
    first = freeze_report(report, tmp_path, check_universe_coverage=False, confirmed=True)
    second = freeze_report(report, tmp_path, check_universe_coverage=False, confirmed=True)
    assert first["status"] == "frozen"
    assert second["status"] == "already_frozen"
    assert (tmp_path / "P-001.json").exists()
    report["code_commit"] = "changed"
    with pytest.raises(FileExistsError):
        freeze_report(report, tmp_path, check_universe_coverage=False, confirmed=True)


def test_freeze_writes_verification_hash(tmp_path):
    result = freeze_report(_report(), tmp_path, check_universe_coverage=False, confirmed=True)
    hash_file = (tmp_path / "P-001.sha256").read_text(encoding="utf-8")
    assert result["sha256"] in hash_file
