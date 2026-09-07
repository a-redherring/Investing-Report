import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from investment_system.ingestion.cnn_fear_greed import fetch_equity_fear_greed
from investment_system.ingestion.data_sources import CnnFearGreedConfig
from investment_system.ingestion.errors import (
    IngestionRateLimitError,
    IngestionResponseError,
    IngestionStaleDataError,
)
from investment_system.snapshots import SnapshotStore

FIXTURES = Path(__file__).parent / "fixtures" / "cnn_fear_greed"
TEST_CONFIG = CnnFearGreedConfig(
    provider="CNN",
    base_url="https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
    user_agent="test-agent",
    referer="https://www.cnn.com/markets/fear-and-greed",
    timeout_seconds=10,
    max_age_seconds=345600,
)


def _fresh_reading_bytes(score: float = 41.86, rating: str = "fear") -> bytes:
    now = datetime.now(timezone.utc).isoformat()
    return json.dumps({"fear_and_greed": {"score": score, "rating": rating, "timestamp": now}}).encode("utf-8")


def _transport_returning(content: bytes):
    def transport(request):
        assert "Referer" in request.headers  # bot-blocking workaround must actually be sent
        return content
    return transport


def _raising_transport(exc: Exception):
    def transport(request):
        raise exc
    return transport


def test_successful_reading_is_parsed_and_snapshotted(tmp_path):
    raw = _fresh_reading_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        observation = fetch_equity_fear_greed(snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))
        assert observation.value == 41.86
        assert observation.category == "fear"
        assert observation.provider == "CNN"
        snapshot = store.list(source="cnn:fear_and_greed")
        assert len(snapshot) == 1
        assert snapshot[0].content == raw.decode("utf-8")


def test_bot_block_response_is_rejected_and_still_snapshotted(tmp_path):
    # Regression test: an unauthenticated request to this endpoint really
    # does return this exact plain-text response (confirmed 2026-09-07),
    # not JSON -- must be a clean IngestionResponseError, not a crash.
    raw = (FIXTURES / "teapot.txt").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="likely blocked as a bot"):
            fetch_equity_fear_greed(snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))
        assert len(store.list(source="cnn:fear_and_greed")) == 1  # evidence preserved even though ultimately rejected


def test_missing_fear_and_greed_key_is_rejected(tmp_path):
    raw = (FIXTURES / "missing_key.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="missing 'fear_and_greed'"):
            fetch_equity_fear_greed(snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))


def test_missing_score_field_is_rejected(tmp_path):
    raw = (FIXTURES / "missing_score.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="missing/malformed fields"):
            fetch_equity_fear_greed(snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))


def test_stale_reading_is_rejected_and_still_snapshotted(tmp_path):
    raw = (FIXTURES / "stale.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionStaleDataError, match="old"):
            fetch_equity_fear_greed(snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))
        assert len(store.list(source="cnn:fear_and_greed")) == 1


def test_rate_limit_is_a_distinct_error(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionRateLimitError):
            fetch_equity_fear_greed(
                snapshot_store=store,
                config=TEST_CONFIG,
                transport=_raising_transport(IngestionRateLimitError("HTTP 429")),
            )


def test_load_cnn_fear_greed_config_reads_committed_yaml():
    from investment_system.ingestion.data_sources import load_cnn_fear_greed_config

    config = load_cnn_fear_greed_config()
    assert config.provider == "CNN"
    assert config.referer == "https://www.cnn.com/markets/fear-and-greed"
