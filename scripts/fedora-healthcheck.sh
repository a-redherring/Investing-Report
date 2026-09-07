#!/usr/bin/env bash
set -euo pipefail

repo_dir="${INVESTMENT_SYSTEM_REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$repo_dir"

command -v python >/dev/null || { echo "python is required" >&2; exit 1; }
python -m compileall -q src tests
PYTHONPATH=src python -m investment_system.cli config >/dev/null
PYTHONPATH=src python -m investment_system.cli signals tests/fixtures/prices.csv >/dev/null
PYTHONPATH=src python -m investment_system.cli validate-report reports/practice/P-001.example.json --no-universe-check >/dev/null
echo "Fedora installation healthcheck passed"
