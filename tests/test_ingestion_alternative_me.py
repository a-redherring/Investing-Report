import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from investment_system.ingestion.alternative_me import fetch_crypto_fear_greed
from investment_system.ingestion.data_sources import AlternativeMeConfig
from investment_system.ingestion.errors import (
    IngestionRateLimitError,
    IngestionResponseError,
    IngestionStaleDataError,
)
from investment_system.snapshots import SnapshotStore

FIXTURES = Path(__file__).parent / "fixtures" / "alternative_me"
TEST_CONFIG = AlternativeMeConfig(
    provider="Alternative.me",
    base_url="https://api.alternative.me/fng",
    timeout_seconds=10,
    max_age_seconds=172800,
)


def _fresh_reading_bytes(value: str = "71", classification: str = "Greed") -> bytes:
    now = int(datetime.now(timezone.utc).timestamp())
    return json.dumps({"data": [{"value": value, "value_classification": classification, "timestamp": str(now)}], "metadata": {"error": None}}).encode("utf-8")


def _transport_returning(content: bytes):
    def transport(request):
        return content
    return transport


def _raising_transport(exc: Exception):
    def transport(request):
        raise exc
    return transport


def test_successful_reading_is_parsed_and_snapshotted(tmp_path):
    raw = _fresh_reading_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        observation = fetch_crypto_fear_greed(snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))
        assert observation.value == 71.0
        assert observation.category == "Greed"
        assert observation.provider == "Alternative.me"
        snapshot = store.list(source="alternative_me:fng")
        assert len(snapshot) == 1
        assert snapshot[0].content == raw.decode("utf-8")


def test_empty_data_is_rejected(tmp_path):
    raw = (FIXTURES / "fng_empty.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="no 'data' entries"):
            fetch_crypto_fear_greed(snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))


def test_malformed_fields_are_rejected_and_still_snapshotted(tmp_path):
    raw = (FIXTURES / "fng_malformed.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="missing/malformed fields"):
            fetch_crypto_fear_greed(snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))
        assert len(store.list(source="alternative_me:fng")) == 1  # evidence preserved even though ultimately rejected


def test_stale_reading_is_rejected_and_still_snapshotted(tmp_path):
    raw = (FIXTURES / "fng_stale.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionStaleDataError, match="old"):
            fetch_crypto_fear_greed(snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))
        assert len(store.list(source="alternative_me:fng")) == 1


def test_malformed_json_is_rejected(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="not valid JSON"):
            fetch_crypto_fear_greed(snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(b"not json"))


def test_rate_limit_is_a_distinct_error(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionRateLimitError):
            fetch_crypto_fear_greed(
                snapshot_store=store,
                config=TEST_CONFIG,
                transport=_raising_transport(IngestionRateLimitError("HTTP 429")),
            )


def test_load_alternative_me_config_reads_committed_yaml():
    from investment_system.ingestion.data_sources import load_alternative_me_config

    config = load_alternative_me_config()
    assert config.provider == "Alternative.me"
    assert config.base_url == "https://api.alternative.me/fng"
