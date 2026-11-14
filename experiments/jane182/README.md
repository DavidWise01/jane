# JANE 182 — The Log That Must Grow Honestly

**Invariant:** Linked checkpoints do not prove append-only growth.

`consistency.py` implements a bounded explicit-prefix consistency proof. Each leaf of the old signed checkpoint is provided and verified at its original index in the new signed checkpoint using a SHA-256 Merkle inclusion path. The old root is recomputed from the complete supplied prefix, while both roots bind the **exact tree size**. This is O(n log n), not the compact RFC 6962 consistency proof.

The synthetic demonstration grows 6 entries to 9 while preserving the first 6. The engine detects modified, reordered or omitted old leaves; forged signatures, replay, rollback, malformed paths, and tampered local logs. Three fixture custodians sign each checkpoint with Ed25519, but they do not establish independent operators or physical timing.

The local SQLite hash chain needs a separately retained head to detect clean truncation. Jane's active parent remains frozen and no learning is applied.

Run: `python -m unittest -q test_consistency.py` (37 tests), then `python consistency.py`.

Next natural bound — JANE 183: Compact Prefix Proof. Compare a logarithmic consistency witness against this explicit verifier across bounded randomized histories.