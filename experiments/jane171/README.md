# JANE 171 — Shared Sensor Ancestry

**Invariant:** Three signed reports do not prove three independently originated measurements.

The engine `lineage.py` resolves a directed dependency graph through sensors, brokers, and calibration intermediaries to declared measurement roots. It computes a maximum set of reports with pairwise-disjoint measurement ancestry; overlap prevents duplicate evidence from meeting a 3-root fixture threshold.

This is **not** independent operational proof. Input nodes are unsiged, user-supplied fixtures; `signature_verification_performed=false` and `operational_independence_verified=false`. The graph cannot authenticate actual physical lineage. All promotion remains frozen.

Results: three different reports, keys, and administrators sharing a broker resolve to **one declared measurement root**, status `SHARED_MEASUREMENT_ANCESTRY`; three separately rooted fixtures resolve to `DECLARED_ROOT_QUORUM`. The latter is a *synthetic graph judgment only*, not a production quorum.

Other checks include duplicate reports, staleness, missing ancestry, cycles, depth limit, conflicting conditions, bounded combinatorial search, and locally hash-linked audit records. Hash-chains cannot detect clean truncation without an external remembered head.

Run from experiment directory: `python -m unittest -v test_lineage.py` (35 tests); `python lineage.py` prints fixture results.

## Next natural bound — JANE 172
Authenticate measurement-lineage *edges* using separately signed source receipts. A self-declared broker graph must not be promoted to verified provenance.