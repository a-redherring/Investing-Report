import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from investment_system.ingestion.data_sources import FinnhubConfig, load_finnhub_config
from investment_system.ingestion.errors import (
    IngestionConfigError,
    IngestionRateLimitError,
    IngestionResponseError,
    IngestionStaleDataError,
)
from investment_system.ingestion.finnhub import fetch_quote
from investment_system.snapshots import SnapshotStore

FIXTURES = Path(__file__).parent / "fixtures" / "finnhub"
TEST_CONFIG = FinnhubConfig(
    provider="Finnhub",
    base_url="https://finnhub.io/api/v1",
    api_key_env_var="FINNHUB_API_KEY",
    timeout_seconds=10,
    max_quote_age_seconds=3600,
)


def _fresh_quote_bytes() -> bytes:
    now = int(datetime.now(timezone.utc).timestamp())
    return json.dumps({"c": 261.74, "d": -0.82, "dp": -0.31, "h": 263.31, "l": 260.68, "o": 261.07, "pc": 262.56, "t": now}).encode("utf-8")


def _transport_returning(content: bytes):
    def transport(request):
        assert "X-Finnhub-Token" in request.headers or "X-finnhub-token" in request.headers
        assert "token=" not in request.full_url  # the key must never be in the URL
        return content
    return transport


def _raising_transport(exc: Exception):
    def transport(request):
        raise exc
    return transport


def test_missing_api_key_fails_closed_and_never_calls_transport(tmp_path, monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)

    def transport(request):
        raise AssertionError("transport must not be called without an API key")

    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionConfigError, match="FINNHUB_API_KEY"):
            fetch_quote("AAPL", snapshot_store=store, config=TEST_CONFIG, transport=transport)


def test_successful_quote_is_parsed_and_snapshotted(tmp_path):
    raw = _fresh_quote_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        quote = fetch_quote("AAPL", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(raw))
        assert quote.symbol == "AAPL"
        assert quote.current == 261.74
        assert quote.previous_close == 262.56
        snapshot = store.get(quote.snapshot_id)
        assert snapshot.content == raw.decode("utf-8")
        assert snapshot.source == "finnhub:quote:AAPL"


def test_api_key_header_used_not_url(tmp_path):
    raw = _fresh_quote_bytes()
    seen = {}

    def transport(request):
        seen["headers"] = dict(request.headers)
        seen["url"] = request.full_url
        return raw

    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        fetch_quote("AAPL", snapshot_store=store, api_key="super-secret", config=TEST_CONFIG, transport=transport)
    assert "super-secret" not in seen["url"]
    assert seen["headers"].get("X-finnhub-token") == "super-secret"


def test_rate_limit_is_a_distinct_error(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionRateLimitError):
            fetch_quote(
                "AAPL",
                snapshot_store=store,
                api_key="test-key",
                config=TEST_CONFIG,
                transport=_raising_transport(IngestionRateLimitError("HTTP 429")),
            )


def test_malformed_json_is_snapshotted_before_being_rejected(tmp_path):
    raw = (FIXTURES / "quote_not_json.txt").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="not valid JSON"):
            fetch_quote("AAPL", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(raw))
        saved = store.list(source="finnhub:quote:AAPL")
        assert len(saved) == 1
        assert saved[0].content == raw.decode("utf-8")


def test_missing_fields_is_rejected(tmp_path):
    raw = (FIXTURES / "quote_missing_fields.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="missing fields"):
            fetch_quote("AAPL", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(raw))


def test_all_zero_response_is_treated_as_unrecognized_symbol(tmp_path):
    raw = (FIXTURES / "quote_zero.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="unrecognized symbol"):
            fetch_quote("NOTASYMBOL", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(raw))


def test_stale_quote_is_snapshotted_before_being_rejected(tmp_path):
    raw = (FIXTURES / "quote_stale.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionStaleDataError, match="old"):
            fetch_quote("AAPL", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(raw))
        saved = store.list(source="finnhub:quote:AAPL")
        assert len(saved) == 1  # evidence preserved even though ultimately rejected


def test_empty_symbol_is_rejected(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionConfigError, match="symbol"):
            fetch_quote("   ", snapshot_store=store, api_key="test-key", config=TEST_CONFIG, transport=_transport_returning(b"{}"))


def test_load_finnhub_config_reads_committed_yaml():
    config = load_finnhub_config()
    assert config.provider == "Finnhub"
    assert config.api_key_env_var == "FINNHUB_API_KEY"
    assert config.base_url == "https://finnhub.io/api/v1"


def test_load_finnhub_config_missing_source_fails_closed(tmp_path):
    path = tmp_path / "data-sources.yaml"
    path.write_text("sources: {}\n")
    with pytest.raises(IngestionConfigError, match="finnhub"):
        load_finnhub_config(path)
