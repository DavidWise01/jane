# JANE 172 — The Provenance of the Provenance

## Invariant

A declared measurement lineage is not an authenticated measurement lineage. Each custody/measurement dependence edge must be supported by **both endpoint principals' Ed25519 signatures** over the canonical edge record. Valid edge signatures authenticate a *claim* and do **not** prove a true physical measurement or organizational independence.

## Engine

`lineage_auth.py` verifies dual signatures, exact versioned canonical edge schemas, declared roles, freshness, per-child nonce replay, single-parent consistency, graph cycles, missing lineage, and search budget. It traces each sensor to its claimed physical measurement source. Shared upstream paths count once. Failure is fail-closed: any invalid receipt or incomplete chain disables a quorum conclusion. It preserves per-edge audit events in a hash-linked ledger. Local-chain integrity does not detect clean truncation without an externally retained head.

## Tests

Run: `cd experiments/jane172 && python -m unittest -v test_lineage_auth.py`.

38 local regression tests include forged child and parent signatures, tampering, conflicting parents, cycles, freshness, replay, missing links, shared roots, distinct roots, and unchanged active parent.

## Fixture demonstration

Three sensors linked through one signed broker → one declared root, `SHARED_MEASUREMENT_ANCESTRY`.
Three sensors with signed links to separate source keys → three declared roots, `DECLARED_ROOT_QUORUM`. `independence_verified` remains `false` in both cases.

All keys, roles, administrators, relationships, and clocks are local fixtures. No real-world independent measurement, trusted hardware attestation, remote custody, or autonomous Jane activation is implied. A production protocol must verify physical binding and administrator independence separately.

## Next natural bound: JANE 173
A dual-signed lineage edge may still be false if both signers collude. Correlate edge receipts with independently retained acquisition evidence and expose the uncertainty of physical-source identity.