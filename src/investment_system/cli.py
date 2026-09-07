from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

from .candidates import assemble_candidates
from .engine import calculate_signals, config_snapshot, cost_table, validate_report
from .ingestion.alternative_me import fetch_crypto_fear_greed
from .ingestion.cnn_fear_greed import fetch_equity_fear_greed
from .ingestion.errors import IngestionError
from .ingestion.finnhub import fetch_quote
from .ingestion.yahoo import fetch_weekly_history as fetch_yahoo_weekly_history
from .snapshots import DEFAULT_DB_PATH, SnapshotStore
from .reports import freeze_report

_SENTIMENT_FETCHERS = {
    "equity": fetch_equity_fear_greed,
    "crypto": fetch_crypto_fear_greed,
}

# Only assets with an unambiguous, already-verified provider mapping are
# listed here. GOLD tracks ASX:GOLD (Global X Physical Gold, unhedged) --
# an explicit operator decision (2026-09-07, see INVESTMENT_DECISION_SYSTEM.md's
# "Decisions already made"), not a silent inference from the placeholder
# symbol already in config/universe.yaml. CASH has no price series to fetch.
#
# default_range is per-asset because Yahoo's "IVV.AX" and "GOLD.AX" history
# is confirmed (2026-09-07) to contain corrupted/anomalous data at longer
# ranges that fails the implausible-jump check -- each is pinned to the
# shortest range found clean while still comfortably covering the 200-week
# MA requirement. Every other ticker here is clean at the full "20y".
_HISTORY_PROVIDERS: dict[str, tuple[str, str]] = {
    "IVV": ("IVV.AX", "10y"),
    "NDQ": ("NDQ.AX", "20y"),
    "VAS": ("VAS.AX", "20y"),
    "VGS": ("VGS.AX", "20y"),
    "IZZ": ("IZZ.AX", "20y"),
    "GOLD": ("GOLD.AX", "15y"),
    "VAE": ("VAE.AX", "20y"),
    "BTC": ("BTC-USD", "20y"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Monday investment decision engine")
    sub = parser.add_subparsers(dest="command", required=True)

    signals = sub.add_parser("signals", help="calculate deterministic signals from weekly CSV")
    signals.add_argument("csv")

    candidates = sub.add_parser("candidates", help="assemble one feature record per universe asset from weekly CSV (not a ranking)")
    candidates.add_argument("csv")

    sub.add_parser("costs", help="show indicative fee schedule")
    sub.add_parser("config", help="show parsed model configuration and universe")

    validate = sub.add_parser("validate-report", help="validate a report JSON file against the schema and business rules")
    validate.add_argument("report_json")
    validate.add_argument("--no-universe-check", action="store_true", help="skip the full-universe-coverage rule")
    validate.add_argument("--snapshot-db", default=None, help="verify input_snapshot_id against this snapshot database")

    freeze = sub.add_parser("freeze-report", help="validate and write a report exactly once")
    freeze.add_argument("report_json")
    freeze.add_argument("--output-dir", default=None, help="destination directory; defaults to reports/live or reports/practice")
    freeze.add_argument("--no-universe-check", action="store_true")
    freeze.add_argument("--confirm-freeze", action="store_true", help="required mutation confirmation")

    snapshot_save = sub.add_parser("snapshot-save", help="store a file as an immutable, provenance-tagged snapshot")
    snapshot_save.add_argument("source", help="a short label for where this content came from, e.g. an asset name or feed id")
    snapshot_save.add_argument("path", help="file whose exact contents will be stored")
    snapshot_save.add_argument("--retrieved-at", default=None, help="ISO 8601 timestamp this content was retrieved (default: now) — set explicitly for a scripted/repeatable save so re-running it is a no-op instead of a new snapshot")
    snapshot_save.add_argument("--metadata", default=None, help="extra provenance as a JSON object string, e.g. '{\"rows\": 42}'")
    snapshot_save.add_argument("--db", default=str(DEFAULT_DB_PATH), help=f"snapshot database path (default: {DEFAULT_DB_PATH})")

    snapshot_get = sub.add_parser("snapshot-get", help="retrieve a stored snapshot by id, including its content")
    snapshot_get.add_argument("snapshot_id")
    snapshot_get.add_argument("--db", default=str(DEFAULT_DB_PATH), help=f"snapshot database path (default: {DEFAULT_DB_PATH})")

    snapshot_list = sub.add_parser("snapshot-list", help="list stored snapshots (metadata only, no content)")
    snapshot_list.add_argument("--source", default=None, help="only list snapshots from this source")
    snapshot_list.add_argument("--db", default=str(DEFAULT_DB_PATH), help=f"snapshot database path (default: {DEFAULT_DB_PATH})")

    fetch = sub.add_parser("fetch-quote", help="fetch, validate, and snapshot a Finnhub quote")
    fetch.add_argument("symbol")
    fetch.add_argument("--db", default=None, help=f"snapshot database path (default: {DEFAULT_DB_PATH}, or $INVESTMENT_SYSTEM_SNAPSHOT_DB if set)")

    fetch_history = sub.add_parser("fetch-history", help="fetch, validate, snapshot, and write weekly price history for a universe asset")
    fetch_history.add_argument("asset", help=f"universe asset symbol with a configured provider: {', '.join(sorted(_HISTORY_PROVIDERS))}")
    fetch_history.add_argument("--range", dest="range_", default=None, help="Yahoo history window, e.g. 20y/10y/5y (default: per-asset, 20y for most, 10y for IVV); override to shorten further if a ticker's older history fails the implausible-jump check")
    fetch_history.add_argument("--output-dir", default="data/history", help="directory to write <ASSET>.csv into (default: data/history)")
    fetch_history.add_argument("--db", default=None, help=f"snapshot database path (default: {DEFAULT_DB_PATH}, or $INVESTMENT_SYSTEM_SNAPSHOT_DB if set)")

    fetch_sentiment = sub.add_parser("fetch-sentiment", help="fetch, validate, and snapshot a Fear & Greed reading")
    fetch_sentiment.add_argument("kind", choices=sorted(_SENTIMENT_FETCHERS), help="which sentiment series to fetch")
    fetch_sentiment.add_argument("--db", default=None, help=f"snapshot database path (default: {DEFAULT_DB_PATH}, or $INVESTMENT_SYSTEM_SNAPSHOT_DB if set)")

    args = parser.parse_args()

    if args.command == "signals":
        result = calculate_signals(args.csv)
    elif args.command == "candidates":
        result = {symbol: asdict(candidate) for symbol, candidate in assemble_candidates(args.csv).items()}
    elif args.command == "costs":
        result = cost_table()
    elif args.command == "config":
        result = config_snapshot()
    elif args.command == "validate-report":
        with open(args.report_json, encoding="utf-8") as handle:
            report = json.load(handle)
        outcome = validate_report(report, check_universe_coverage=not args.no_universe_check, snapshot_db=args.snapshot_db)
        result = {
            "valid": outcome.valid,
            "errors": [{"code": issue.code, "message": issue.message} for issue in outcome.errors],
            "warnings": [{"code": issue.code, "message": issue.message} for issue in outcome.warnings],
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        sys.exit(0 if outcome.valid else 1)
    elif args.command == "freeze-report":
        with open(args.report_json, encoding="utf-8") as handle:
            report = json.load(handle)
        if args.output_dir is None:
            kind = report.get("report_kind")
            args.output_dir = "reports/live" if kind == "live" else "reports/practice"
        result = freeze_report(report, args.output_dir, check_universe_coverage=not args.no_universe_check, confirmed=args.confirm_freeze)
    elif args.command == "snapshot-save":
        with open(args.path, encoding="utf-8") as handle:
            content = handle.read()
        metadata = json.loads(args.metadata) if args.metadata else None
        with SnapshotStore(args.db) as store:
            result = store.save(source=args.source, content=content, retrieved_at=args.retrieved_at, metadata=metadata).summary()
    elif args.command == "snapshot-get":
        with SnapshotStore(args.db) as store:
            result = asdict(store.get(args.snapshot_id))
    elif args.command == "fetch-quote":
        db_path = args.db or os.environ.get("INVESTMENT_SYSTEM_SNAPSHOT_DB") or str(DEFAULT_DB_PATH)
        try:
            with SnapshotStore(db_path) as store:
                result = asdict(fetch_quote(args.symbol, snapshot_store=store))
        except IngestionError as exc:
            print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, indent=2, sort_keys=True))
            sys.exit(1)
    elif args.command == "fetch-history":
        asset = args.asset.strip().upper()
        mapping = _HISTORY_PROVIDERS.get(asset)
        if mapping is None:
            print(json.dumps({"error": "UnsupportedAsset", "message": f"no historical-ingestion provider configured for {asset!r}; see docs/wiki/ingestion.md"}, indent=2, sort_keys=True))
            sys.exit(1)
        provider_symbol, default_range = mapping
        range_ = args.range_ or default_range
        db_path = args.db or os.environ.get("INVESTMENT_SYSTEM_SNAPSHOT_DB") or str(DEFAULT_DB_PATH)
        try:
            with SnapshotStore(db_path) as store:
                bars = fetch_yahoo_weekly_history(provider_symbol, snapshot_store=store, range_=range_)
        except IngestionError as exc:
            print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, indent=2, sort_keys=True))
            sys.exit(1)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = output_dir / f"{asset}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["asset", "date", "close"])
            for bar in bars:
                writer.writerow([asset, bar.date, bar.close])
        result = {"asset": asset, "provider": "yahoo", "provider_symbol": provider_symbol, "bars": len(bars), "path": str(csv_path)}
    elif args.command == "fetch-sentiment":
        db_path = args.db or os.environ.get("INVESTMENT_SYSTEM_SNAPSHOT_DB") or str(DEFAULT_DB_PATH)
        fetcher = _SENTIMENT_FETCHERS[args.kind]
        try:
            with SnapshotStore(db_path) as store:
                result = asdict(fetcher(snapshot_store=store))
        except IngestionError as exc:
            print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, indent=2, sort_keys=True))
            sys.exit(1)
    else:
        with SnapshotStore(args.db) as store:
            result = [snapshot.summary() for snapshot in store.list(source=args.source)]
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
