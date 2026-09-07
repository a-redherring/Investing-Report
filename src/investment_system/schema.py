from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from .config import resolve_repo_root

SCHEMA_RELATIVE_PATH = "schemas/frozen-report.schema.json"


def load_schema(path: str | Path | None = None) -> dict[str, object]:
    schema_path = Path(path) if path is not None else resolve_repo_root(SCHEMA_RELATIVE_PATH) / SCHEMA_RELATIVE_PATH
    return json.loads(schema_path.read_text(encoding="utf-8"))


def schema_errors(report: dict[str, object], schema: dict[str, object] | None = None) -> list[str]:
    """Return human-readable JSON Schema violations, sorted for stable output."""
    validator = jsonschema.Draft202012Validator(
        schema or load_schema(), format_checker=jsonschema.FormatChecker()
    )
    return sorted(f"{'/'.join(str(p) for p in error.path) or '<root>'}: {error.message}" for error in validator.iter_errors(report))
