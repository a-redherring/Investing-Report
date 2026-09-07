from pathlib import Path

import pytest

from investment_system.ingestion.data_sources import YahooConfig
from investment_system.ingestion.errors import (
    IngestionConfigError,
    IngestionRateLimitError,
    IngestionResponseError,
)
from investment_system.ingestion.yahoo import fetch_weekly_history
from investment_system.snapshots import SnapshotStore

FIXTURES = Path(__file__).parent / "fixtures" / "yahoo"
TEST_CONFIG = YahooConfig(
    provider="Yahoo Finance",
    base_url="https://query1.finance.yahoo.com/v8/finance/chart",
    user_agent="test-agent",
    timeout_seconds=10,
)


def _transport_returning(content: bytes):
    def transport(request):
        assert "User-agent" in request.headers or "User-Agent" in request.headers
        return content
    return transport


def _raising_transport(exc: Exception):
    def transport(request):
        raise exc
    return transport


def test_successful_history_is_parsed_snapshotted_and_drops_null_bars(tmp_path):
    raw = (FIXTURES / "chart_ivv_ax.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        bars = fetch_weekly_history("IVV.AX", snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))
        # The fixture has 4 timestamps but a null close on the last one --
        # that in-progress bar must be dropped, not substituted with a guess.
        assert len(bars) == 3
        assert [bar.close for bar in bars] == [100.0, 101.5, 102.25]
        assert bars[0].date == "2024-01-01"
        snapshot = store.list(source="yahoo:chart:IVV.AX")
        assert len(snapshot) == 1
        assert snapshot[0].content == raw.decode("utf-8")


def test_error_response_is_rejected_and_still_snapshotted(tmp_path):
    raw = (FIXTURES / "chart_error.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="Not Found"):
            fetch_weekly_history("NOTASYMBOL", snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))
        saved = store.list(source="yahoo:chart:NOTASYMBOL")
        assert len(saved) == 1  # evidence preserved even though ultimately rejected


def test_implausible_week_over_week_jump_is_rejected(tmp_path):
    # Regression test for real corrupted data found 2026-09-07: Yahoo's
    # "IVV.AX" history repeatedly flip-flopped ~15x between real and bogus
    # values throughout 2010-2017. A single-week move beyond the sanity
    # bound must be rejected outright, not silently fed to indicators.
    raw = (FIXTURES / "chart_implausible_jump.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="implausible week-over-week move"):
            fetch_weekly_history("IVV.AX", snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))


def test_a_real_extreme_crash_is_not_rejected(tmp_path):
    # A genuine, large single-week decline (e.g. BTC's real ~-33% COVID-crash
    # week) must NOT trip the corrupted-data check -- only implausible moves
    # far beyond real market volatility should.
    raw = b'{"chart":{"result":[{"meta":{},"timestamp":[1704067200,1704672000],"indicators":{"quote":[{"close":[8108.12,5392.31]}]}}],"error":null}}'
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        bars = fetch_weekly_history("BTC-USD", snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))
        assert [bar.close for bar in bars] == [8108.12, 5392.31]


def test_missing_timestamp_or_close_data_is_rejected(tmp_path):
    raw = (FIXTURES / "chart_missing_data.json").read_bytes()
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="missing timestamp/close data"):
            fetch_weekly_history("IVV.AX", snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(raw))


def test_malformed_json_is_rejected(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionResponseError, match="not valid JSON"):
            fetch_weekly_history("IVV.AX", snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(b"not json"))


def test_rate_limit_is_a_distinct_error(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionRateLimitError):
            fetch_weekly_history(
                "IVV.AX",
                snapshot_store=store,
                config=TEST_CONFIG,
                transport=_raising_transport(IngestionRateLimitError("HTTP 429")),
            )


def test_empty_symbol_is_rejected(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(IngestionConfigError, match="symbol"):
            fetch_weekly_history("   ", snapshot_store=store, config=TEST_CONFIG, transport=_transport_returning(b"{}"))


def test_load_yahoo_config_reads_committed_yaml():
    from investment_system.ingestion.data_sources import load_yahoo_config

    config = load_yahoo_config()
    assert config.provider == "Yahoo Finance"
    assert config.base_url == "https://query1.finance.yahoo.com/v8/finance/chart"
