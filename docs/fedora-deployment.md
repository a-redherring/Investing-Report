# Fedora deployment

Fedora is the supported development, test, and production platform. The
desktop test machine should use the same virtual-environment, filesystem,
environment-file, SQLite, and systemd layout as the home server.

## Current healthcheck

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
./scripts/fedora-healthcheck.sh
```

The healthcheck is offline. It compiles the package, loads configuration,
calculates fixture signals, and validates the illustrative practice report. It
does not call Finnhub and does not create a live report.

Reports can now be frozen explicitly after validation:

```bash
PYTHONPATH=src python -m investment_system.cli freeze-report \
  reports/practice/P-001.example.json \
  --output-dir /tmp/practice-reports \
  --no-universe-check \
  --confirm-freeze
```

Freezing writes canonical JSON and a SHA-256 sidecar once. A later attempt to
overwrite the same report ID with different content fails. Live reports should
not be frozen until the full universe, data snapshot, and Monday checks pass.

## Planned home-server layout

```text
/opt/investing-advice/
  repo/
  venv/

/etc/investing-advice/
  secrets.env
```

Create a dedicated service account and keep secrets outside Git:

```bash
sudo useradd --system --home-dir /opt/investing-advice --shell /sbin/nologin investing
sudo install -d -o investing -g investing /opt/investing-advice
sudo install -d -o root -g investing -m 0750 /etc/investing-advice
sudo install -o root -g investing -m 0640 .env.example /etc/investing-advice/secrets.env
sudoedit /etc/investing-advice/secrets.env
```

Set `FINNHUB_API_KEY` in that file. Do not put the actual key in the
repository, systemd unit, command line, logs, reports, or GitHub issues.

## systemd templates

[`deploy/systemd/investment-system.service.example`](../deploy/systemd/investment-system.service.example)
and [`investment-system.timer.example`](../deploy/systemd/investment-system.timer.example)
are templates for the eventual Monday runner. They intentionally reference
`investment-system monday-run`, which does not exist yet. Do not enable them
until the ingestion and report pipeline has been implemented and tested.

When ready:

```bash
sudo cp deploy/systemd/investment-system.service.example /etc/systemd/system/investment-system.service
sudo cp deploy/systemd/investment-system.timer.example /etc/systemd/system/investment-system.timer
sudo systemctl daemon-reload
sudo systemctl enable --now investment-system.timer
systemctl list-timers investment-system.timer
```

The service is intended to be outbound-only, local SQLite/Markdown/JSON, and
STDIO MCP. It must fail closed on missing credentials, network errors, stale or
incomplete data, and failed validation. It must never place trades.
