# JANE 164 — The Checkpoint That Survives

**Invariant:** A locally valid hash history can be cleanly truncated. Compare it to an Ed25519-signed checkpoint retained outside the returned local history.

`anchor.py` provides the chain verifier, deterministic fixture signing, separate `AnchorStore` SQLite database, nonce-replay and same-root fork detection, and audit against retained checkpoint receipts. It refuses insufficient declared administrative roots, invalid signatures, conflicting heads, and missing anchored suffixes.

Run: `python -m unittest -v test_anchor.py` (39 tests). `python anchor.py` prints demonstration results.

**Scope:** All custodian keys, administrators and SQLite files are local deterministic fixtures. They are not real-world independent custodians, nor proof of physical scheduler execution. `VALID_EXTENSION` means an extension preserves the most recently supplied anchors; it does not assert that no newer anchor exists elsewhere. External independently held heads are required for protection from deletion or replacement of the anchor store itself. Jane's active parent is not changed.

## Next natural bound — JANE 165
**Anchor freshness and completeness:** A perfectly matching but stale external checkpoint cannot prove a history is current. Detect freshness windows and distinguish certified historic continuity from current completeness.