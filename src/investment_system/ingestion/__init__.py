"""Live market-data ingestion adapters.

Each adapter (see finnhub.py) follows the same contract: fail closed on a
missing credential, transport/HTTP failure, malformed or stale response; never
call the network from a unit test (the HTTP transport is dependency-injected,
so tests supply a fake); and record full provenance -- source, endpoint,
retrieval time, response hash, snapshot id -- via
investment_system.snapshots.SnapshotStore for every fetch attempt, including
ones ultimately rejected as malformed or stale, so the raw evidence is never
lost.

Nothing in this package produces a ranking, a score, or a buy/sell
recommendation, and nothing here bears on any asset's hard-gate/risk status
(e.g. BTCB2's blake2b_gate) -- it only produces a validated,
provenance-tagged data point for something else to use later.
"""
