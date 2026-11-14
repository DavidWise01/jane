# JANE 187 — The Watermark That Cannot Be Trusted

**Invariant:** Signed watermark ≠ proven sequence coverage.

FLAY verifies an Ed25519-signed sender manifest, Ed25519-signed individual receiver acknowledgments, and a receiver-signed watermark bound to an **ordered size-bound Merkle inbox commitment**. It checks every expected sequence from sender `start` through `end` before reporting fixture-level coverage. A signed watermark over a subset like `[1,3]` with `through=3` returns `WATERMARK_COVERAGE_GAP` with missing `[2]` even when every signature and the Merkle commitment are valid.

## Boundaries
- Complete snapshots are bounded to 256 acknowledgments.
- Forged signatures, duplicate/conflicting acknowledgments, wrong payload digests, mismatched commitments, stale watermark timestamps, and nonce replay are rejected.
- SQLite preserves used watermark nonces across restarts and records a local hash-linked event history.
- **Local hash-chain truncation still requires an externally retained head to detect.**
- **A signed receiver claim is not proof of physical delivery or independent source custody.** A malicious receiver controlling its key may sign a false complete snapshot; independent observations are a separate engineering boundary.
- Jane's active parent is frozen. No automatic learning or live scheduler modifications.

## Run
```
python -m unittest -v test_coverage.py
python coverage.py
```

## Next natural bound — JANE 188: The Inbox That Can Be Fabricated
A receiver can sign a *complete* fictional inbox. Compare receiver-signed processing claims with separately witnessed processing effects and content-addressed storage, without conflating signatures with actual physical execution.
