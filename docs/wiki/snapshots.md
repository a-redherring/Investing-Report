# Snapshots

`src/investment_system/snapshots.py` (`SnapshotStore`) is the "immutable raw
snapshot storage" from `INVESTMENT_DECISION_SYSTEM.md`'s Phase 1 data
foundation — deliberately decoupled from any specific data source. The
repository has one live adapter, Finnhub single quotes, which snapshots raw
responses before validating them; this store remains reusable by future
adapters and the deterministic CSV path.

## What it guarantees

- **Append-only.** No method ever issues `UPDATE` or `DELETE`, and SQLite
  triggers reject direct update/delete attempts on the table.
- **Content-identified.** A snapshot's id is `sha256(source + retrieved_at +
  content)`. Saving the exact same `(source, retrieved_at, content)` twice is
  a harmless no-op (same id, same row, `stored_at` unchanged) — safe to call
  from an idempotent/retried job. Any change to `content` produces a **new**
  row with a new id; the old row is never touched.
- **Provenance-first.** Every row records `source`, `retrieved_at` (when the
  data was as-of/retrieved — caller-supplied, defaults to now), `stored_at`
  (when this process actually wrote the row), and a `content_sha256` (so a
  reader can verify integrity without re-deriving the snapshot id).
- **Local SQLite**, one file, no server — matches the design doc's
  zero-additional-cost/local-first guardrails. Default path:
  `data/snapshots.sqlite3` (already gitignored, alongside `data/*.db`).

## API

```python
from investment_system.snapshots import SnapshotStore

with SnapshotStore("data/snapshots.sqlite3") as store:
    snap = store.save(
        source="asx-ivv-weekly",
        content=csv_text,
        retrieved_at="2026-09-07T08:00:00+10:00",  # optional; omit for now()
        metadata={"rows": 210},                      # optional, free-form
    )
    store.get(snap.snapshot_id)             # -> Snapshot (raises KeyError if missing)
    store.list(source="asx-ivv-weekly")     # -> list[Snapshot], oldest first
    snap.summary()                          # dict of every field except `content`
```

## CLI

```bash
investment-system snapshot-save <source> <path> [--retrieved-at ISO8601] [--metadata '{"k": "v"}'] [--db PATH]
investment-system snapshot-get <snapshot_id> [--db PATH]
investment-system snapshot-list [--source NAME] [--db PATH]
```

`snapshot-save`/`-get` print the full snapshot including `content`;
`snapshot-list` prints only `summary()` for every match (no `content`) so
listing many/large snapshots stays readable. `--db` defaults to
`data/snapshots.sqlite3`; pass a `--retrieved-at` explicitly for a
scripted/repeatable save (otherwise every manual CLI invocation mints a fresh
`retrieved_at` and is correctly recorded as a distinct provenance event, not
deduplicated). `make smoke` exercises this with a fixed old `--retrieved-at`
so repeated runs stay idempotent rather than accumulating rows.

## What's NOT here yet

- Finnhub quote fetching snapshots its raw response automatically, including
  malformed or stale responses, so rejected data remains auditable.
  `calculate_signals()` does not snapshot its input CSV before reading it;
  wiring historical ingestion into the technical pipeline is future work.
- No pruning/retention policy — the store is genuinely append-only forever.
  Fine for a personal research tool at today's scale; revisit if that changes.
- `engine.validate_report()` can verify a frozen report's `input_snapshot_id`
  against this store when called with `snapshot_db=...`; the CLI exposes this
  as `--snapshot-db`. Automatic population during ingestion is still future
  work.
