.PHONY: build test smoke

build:
	python -m compileall -q src tests

test:
	python -m pytest -q

smoke:
	PYTHONPATH=src python -m investment_system.cli costs
	PYTHONPATH=src python -m investment_system.cli config
	PYTHONPATH=src python -m investment_system.cli signals tests/fixtures/prices.csv
	PYTHONPATH=src python -m investment_system.cli validate-report reports/practice/P-001.example.json --no-universe-check
	PYTHONPATH=src python -m investment_system.cli snapshot-save fixture-prices tests/fixtures/prices.csv --retrieved-at 2000-01-01T00:00:00+00:00 --metadata '{"purpose": "smoke test"}'
	PYTHONPATH=src python -m investment_system.cli snapshot-list --source fixture-prices
	PYTHONPATH=src python -m investment_system.cli freeze-report reports/practice/P-001.example.json --output-dir /tmp/investment-system-practice --no-universe-check --confirm-freeze
