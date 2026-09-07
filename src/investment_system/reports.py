"""Append-only frozen report storage."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .engine import validate_report


def canonical_json(report: dict[str, object]) -> bytes:
    return (json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def freeze_report(report: dict[str, object], output_dir: str | Path, *, check_universe_coverage: bool = True, confirmed: bool = False) -> dict[str, object]:
    """Validate and write a report exactly once, returning its hash metadata.

    Mutation requires ``confirmed=True``. Existing report IDs are never
    overwritten, even when the proposed content differs.
    """
    if not confirmed:
        raise ValueError("freezing a report requires explicit confirmation")
    outcome = validate_report(report, check_universe_coverage=check_universe_coverage)
    if not outcome.valid:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in outcome.errors)
        raise ValueError(f"report is not valid: {details}")
    report_id = str(report["report_id"])
    filename = f"{report_id}.json"
    destination = Path(output_dir) / filename
    payload = canonical_json(report)
    report_hash = hashlib.sha256(payload).hexdigest()
    hash_path = destination.with_suffix(".sha256")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing = destination.read_bytes()
        if existing != payload:
            raise FileExistsError(f"frozen report {report_id} already exists with different content")
        return {"report_id": report_id, "path": str(destination), "sha256": report_hash, "status": "already_frozen"}
    destination.write_bytes(payload)
    hash_path.write_text(f"{report_hash}  {filename}\n", encoding="utf-8")
    return {"report_id": report_id, "path": str(destination), "sha256": report_hash, "status": "frozen"}
