"""Append-only, provenance-bearing storage for raw input snapshots.

This is the "immutable raw snapshot storage" from
INVESTMENT_DECISION_SYSTEM.md's Phase 1 data foundation, decoupled from any
specific data source (see docs/wiki/ingestion.md for the one adapter that
currently uses it). It only provides the storage primitive: given some raw
content plus who/when it came from, record it so it can never be silently
overwritten, and retrieve it later by id.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = Path("data") / "snapshots.sqlite3"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    stored_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS snapshots_no_update
BEFORE UPDATE ON snapshots
BEGIN
    SELECT RAISE(ABORT, 'snapshots are append-only');
END;
CREATE TRIGGER IF NOT EXISTS snapshots_no_delete
BEFORE DELETE ON snapshots
BEGIN
    SELECT RAISE(ABORT, 'snapshots are append-only');
END;
"""


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    source: str
    retrieved_at: str
    content_sha256: str
    content: str
    metadata: dict[str, object]
    stored_at: str

    def summary(self) -> dict[str, object]:
        """Fields safe to print/list in bulk — everything except the raw content."""
        return {key: value for key, value in asdict(self).items() if key != "content"}


def _snapshot_id(source: str, retrieved_at: str, content: str) -> str:
    # Identity is (source, retrieved_at, content), not content alone: two
    # fetches of unchanged data at different times are distinct provenance
    # events and both get recorded, matching the design doc's requirement to
    # record retrieval time for every observation.
    return hashlib.sha256(f"{source}\n{retrieved_at}\n{content}".encode("utf-8")).hexdigest()


def _row_to_snapshot(row: tuple[str, str, str, str, str, str, str]) -> Snapshot:
    snapshot_id, source, retrieved_at, content_sha256, content, metadata_json, stored_at = row
    return Snapshot(snapshot_id, source, retrieved_at, content_sha256, content, json.loads(metadata_json), stored_at)


class SnapshotStore:
    """Append-only, content-identified store for raw input snapshots.

    No method here ever issues UPDATE or DELETE. A snapshot's id is derived
    from (source, retrieved_at, content), so saving identical inputs twice is
    a harmless no-op, and any change to the content produces a new row rather
    than overwriting the old one — the same "corrections are appended, the
    original remains available" discipline the design doc requires for frozen
    reports, applied to the raw inputs behind them.
    """

    _COLUMNS = "snapshot_id, source, retrieved_at, content_sha256, content, metadata_json, stored_at"

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "SnapshotStore":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def save(self, *, source: str, content: str, retrieved_at: str | None = None, metadata: dict[str, object] | None = None) -> Snapshot:
        if not source.strip():
            raise ValueError("source is required")
        retrieved_at = retrieved_at or datetime.now(timezone.utc).isoformat()
        metadata = metadata or {}
        snapshot_id = _snapshot_id(source, retrieved_at, content)
        content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        stored_at = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            f"INSERT OR IGNORE INTO snapshots ({self._COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (snapshot_id, source, retrieved_at, content_sha256, content, json.dumps(metadata, sort_keys=True), stored_at),
        )
        self._conn.commit()
        return self.get(snapshot_id)

    def get(self, snapshot_id: str) -> Snapshot:
        row = self._conn.execute(f"SELECT {self._COLUMNS} FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)).fetchone()
        if row is None:
            raise KeyError(f"no snapshot with id {snapshot_id!r}")
        return _row_to_snapshot(row)

    def list(self, *, source: str | None = None) -> list[Snapshot]:
        if source is None:
            rows = self._conn.execute(f"SELECT {self._COLUMNS} FROM snapshots ORDER BY stored_at").fetchall()
        else:
            rows = self._conn.execute(f"SELECT {self._COLUMNS} FROM snapshots WHERE source = ? ORDER BY stored_at", (source,)).fetchall()
        return [_row_to_snapshot(row) for row in rows]
