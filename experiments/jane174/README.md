# JANE 174 — The Acquisition That Must Be Reproducible

**Invariant:** Repeatable Claim ≠ Independent Reproduction.

`reproduction.py` verifies Ed25519-signed acquisition receipts, raw byte SHA-256 commitments, an exact procedure identifier, declared sensor ancestry, freshness, bounded measurement tolerance, and persistent `(device,run)` replay records. `test_reproduction.py` contains 45 executable tests.

Fixture example: three distinct declared instrument roots return values 1000, 1002, and 999 milliunits with tolerance ±5 milliunits (maximum minus minimum ≤ 5). The outcome `REPRODUCED_DECLARED_FIXTURE` does **not** establish that the values came from real physical devices. A colliding ancestry root yields `SHARED_ACQUISITION_ANCESTRY`, even when a quorum subset could be found; contradictory values yield `MEASUREMENT_DISAGREEMENT`. Missing raw bytes, mismatched SHA-256, forged signatures, stale claims, duplicate runs, and replay are retained as rejected observations.

Run `python -m unittest -q test_reproduction.py`, `python reproduction.py` from this directory. SQLite journal heads are locally hash linked. Only a separately retained external head can demonstrate a clean suffix truncation. `result.json` is from a local deterministic fixture. Jane's active parent remains frozen and no learning is applied.

## Next natural bound — JANE 175: The Reproduction That Changes the Question

Verify that repeated acquisition used equivalent procedures and comparable samples; detect protocol drift, cherry-picked samples, and false agreement from correlated acquisition conditions.