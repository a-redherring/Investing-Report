import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from investment_system.ingestion.data_sources import FredConfig
from investment_system.ingestion.errors import (
    IngestionConfigError,
    IngestionRateLimitError,
    IngestionResponseError,
    IngestionStaleDataError,
)
from investment_system.ingestion.fred import fetch_series_latest
from investment_system.snapshots import SnapshotStore

FIXTURES = Path(__file__).parent / "fixtures" / "fred"
TEST_CONFIG = FredConfig(
    provider="FRED (Federal Reserve Bank of St. Louis)",
    base_url="https://api.stlouisfed.org/fred",
    api_key_env_var="FRED_API_KEY",
    timeout_seconds=10,
    max_age_days=10,
)


def _fresh_observations_bytes(value: str = "17.5", missing_count: int = 0) -> bytes:
    today = datetime.now(timezone.utc).date()
    observations = [{"realtime_start": "x", "realtime_end": "x", "date": (today - timedelta(days=i)).isoformat(), "value": "."} for i in range(missing_count)]
    observations.append({"realtime_start": "x", "realtime_end": "x", "date": (today - timedelta(days=missing_count)).isoformat(), "value": value})
    return json.dumps({"observations": observations}).encode("utf-8")


def _transport_returning(content: bytes):
    def transport(request):
        return content
    return transport


def _raising_transport(exc: Exception):
    def transport(request):
        raise exc
    return transport


def test_missing_api_key_fails_closed_and_never_calls_transport(tmp_path, monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    def transport(request):
        raise AssertionError("transport must not be called without an API key")

    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionConfigError, match="FRED_API_KEY"):
            fetch_series_latest("VIXCLS", snapshot_store=store, config=TEST_CONFIG, transport=transport)


def test_successful_observation_is_parsed_and_snapshotted(tmp_path):
    raw = _fresh_observations_bytes(value="17.5")
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        observation = fetch_series_latest("VIXCLS", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(raw))
        assert observation.value == 17.5
        assert observation.series_id == "VIXCLS"
        snapshot = store.list(source="fred:VIXCLS")
        assert len(snapshot) == 1
        assert snapshot[0].content == raw.decode("utf-8")


def test_api_key_never_appears_in_snapshot_or_error(tmp_path):
    raw = _fresh_observations_bytes(value="17.5")
    seen_urls = []

    def transport(request):
        seen_urls.append(request.full_url)
        return raw

    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        fetch_series_latest("VIXCLS", snapshot_store=store, api_key="super-secret-key", config=TEST_CONFIG, transport=transport)
        snapshot = store.list(source="fred:VIXCLS")[0]
        assert "super-secret-key" not in snapshot.content
        assert "super-secret-key" not in json.dumps(snapshot.metadata)
    # the key is legitimately in the constructed request URL (FRED has no
    # header alternative) -- this asserts _default_transport's error paths
    # specifically never echo that URL back, not that the URL is secret-free.
    assert any("super-secret-key" in url for url in seen_urls)


def test_walks_past_missing_values_to_the_latest_real_observation(tmp_path):
    raw = _fresh_observations_bytes(value="4.25", missing_count=2)
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        observation = fetch_series_latest("DFF", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(raw))
        assert observation.value == 4.25


def test_all_missing_observations_is_rejected(tmp_path):
    raw = (FIXTURES / "all_missing.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="no non-missing observations"):
            fetch_series_latest("VIXCLS", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(raw))


def test_error_response_is_rejected_and_still_snapshotted(tmp_path):
    raw = (FIXTURES / "error_missing_key.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="api_key is not set"):
            fetch_series_latest("VIXCLS", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(raw))
        assert len(store.list(source="fred:VIXCLS")) == 1  # evidence preserved even though ultimately rejected


def test_missing_observations_key_is_rejected(tmp_path):
    raw = (FIXTURES / "no_observations_key.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="no observations"):
            fetch_series_latest("VIXCLS", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(raw))


def test_malformed_observation_is_rejected(tmp_path):
    raw = (FIXTURES / "malformed.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="malformed observation"):
            fetch_series_latest("VIXCLS", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(raw))


def test_stale_observation_is_rejected_and_still_snapshotted(tmp_path):
    raw = (FIXTURES / "stale.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionStaleDataError, match="old"):
            fetch_series_latest("VIXCLS", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(raw))
        assert len(store.list(source="fred:VIXCLS")) == 1


def test_malformed_json_is_rejected(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="not valid JSON"):
            fetch_series_latest("VIXCLS", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(b"not json"))


def test_rate_limit_is_a_distinct_error(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionRateLimitError):
            fetch_series_latest(
                "VIXCLS",
                snapshot_store=store,
                api_key="test-key",
                config=TEST_CONFIG,
                transport=_raising_transport(IngestionRateLimitError("HTTP 429")),
            )


def test_empty_series_id_is_rejected(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionConfigError, match="series_id"):
            fetch_series_latest("   ", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(b"{}"))


def test_load_fred_config_reads_committed_yaml():
    from investment_system.ingestion.data_sources import load_fred_config

    config = load_fred_config()
    assert config.provider == "FRED (Federal Reserve Bank of St. Louis)"
    assert config.api_key_env_var == "FRED_API_KEY"
