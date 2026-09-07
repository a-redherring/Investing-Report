import hashlib

import pytest

from investment_system.snapshots import SnapshotStore


def test_save_and_get_round_trip(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        snapshot = store.save(source="test-feed", content="asset,date,close\nTEST,2026-01-05,100\n", retrieved_at="2026-01-05T00:00:00+00:00", metadata={"rows": 1})
        fetched = store.get(snapshot.snapshot_id)
        assert fetched == snapshot
        assert fetched.metadata == {"rows": 1}
        assert fetched.content_sha256 == hashlib.sha256(fetched.content.encode("utf-8")).hexdigest()


def test_get_missing_id_raises(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(KeyError):
            store.get("does-not-exist")


def test_saving_identical_inputs_twice_is_idempotent(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        first = store.save(source="test-feed", content="same", retrieved_at="2026-01-05T00:00:00+00:00")
        second = store.save(source="test-feed", content="same", retrieved_at="2026-01-05T00:00:00+00:00")
        assert first.snapshot_id == second.snapshot_id
        assert len(store.list(source="test-feed")) == 1


def test_changed_content_produces_a_new_snapshot_not_an_overwrite(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        first = store.save(source="test-feed", content="v1", retrieved_at="2026-01-05T00:00:00+00:00")
        second = store.save(source="test-feed", content="v2", retrieved_at="2026-01-05T00:00:00+00:00")
        assert first.snapshot_id != second.snapshot_id
        # both remain retrievable — the first was never overwritten
        assert store.get(first.snapshot_id).content == "v1"
        assert store.get(second.snapshot_id).content == "v2"


def test_repeated_fetches_at_different_times_are_distinct_provenance_events(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        first = store.save(source="test-feed", content="unchanged", retrieved_at="2026-01-05T00:00:00+00:00")
        second = store.save(source="test-feed", content="unchanged", retrieved_at="2026-01-12T00:00:00+00:00")
        assert first.snapshot_id != second.snapshot_id
        assert len(store.list(source="test-feed")) == 2


def test_list_filters_by_source_and_orders_by_stored_at(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        store.save(source="feed-a", content="a1", retrieved_at="2026-01-05T00:00:00+00:00")
        store.save(source="feed-b", content="b1", retrieved_at="2026-01-05T00:00:00+00:00")
        store.save(source="feed-a", content="a2", retrieved_at="2026-01-12T00:00:00+00:00")
        feed_a = store.list(source="feed-a")
        assert [s.content for s in feed_a] == ["a1", "a2"]
        assert len(store.list()) == 3


def test_persists_to_disk_across_separate_store_instances(tmp_path):
    db_path = tmp_path / "snap.sqlite3"
    with SnapshotStore(db_path) as store:
        saved = store.save(source="test-feed", content="durable", retrieved_at="2026-01-05T00:00:00+00:00")
    with SnapshotStore(db_path) as reopened:
        assert reopened.get(saved.snapshot_id).content == "durable"


def test_empty_source_is_rejected(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        with pytest.raises(ValueError, match="source"):
            store.save(source="   ", content="x")


def test_summary_excludes_raw_content(tmp_path):
    with SnapshotStore(tmp_path / "snap.sqlite3") as store:
        snapshot = store.save(source="test-feed", content="potentially large payload", retrieved_at="2026-01-05T00:00:00+00:00")
        summary = snapshot.summary()
        assert "content" not in summary
        assert summary["source"] == "test-feed"


def test_sqlite_store_rejects_direct_update_and_delete(tmp_path):
    import sqlite3

    db = tmp_path / "snapshots.db"
    with SnapshotStore(db) as store:
        snapshot = store.save(source="test", content="payload", retrieved_at="2026-01-01T00:00:00+00:00")
        connection = sqlite3.connect(db)
        try:
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute("UPDATE snapshots SET source = 'changed'")
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM snapshots")
        finally:
            connection.close()
        assert store.get(snapshot.snapshot_id).source == "test"


def test_report_can_verify_snapshot_reference(tmp_path):
    import json
    from investment_system.engine import validate_report

    with open("reports/practice/P-001.example.json", encoding="utf-8") as handle:
        report = json.load(handle)
    with SnapshotStore(tmp_path / "snapshots.db") as store:
        snapshot = store.save(source="fixture", content="data", retrieved_at="2026-01-01T00:00:00+00:00")
    report["input_snapshot_id"] = snapshot.snapshot_id
    assert validate_report(report, check_universe_coverage=False, snapshot_db=tmp_path / "snapshots.db").valid
