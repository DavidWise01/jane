# JANE 183 — The Compact Proof

**Invariant:** Smaller proof ≠ weaker verification.

`compact.py` implements a Merkle prefix consistency proof with a domain-separated SHA-256 tree, size-bound root commitments, and Ed25519 fixture checkpoint signatures. The O(log n) proof consists of raw subtree-hash nodes plus a raw old-root opening bound to the signed size-bound old root; it does **not** transmit every prior leaf. This is an RFC 6962-style consistency construction, not a claim of RFC interoperability or production-grade external custody.

### Results

- The 6→9 synthetic checkpoint extension verifies with a compact proof.
- 26 regression tests passed, including 1,000 randomized prefix-growth and adversarial edit checks, plus 300 differential randomized comparisons with the JANE 182 explicit verifier.
- Rewritten, deleted, or reordered prefix leaves are rejected.
- Mismatched sizes, missing/extra/altered proof nodes, forged signatures, duplicate administrative ancestry, rollback, and replay are rejected.
- The append-only local audit needs an externally held head to detect clean truncation. Fixture witness roots are **not** verified independent custodians. No Jane parent activation or automatic learning.

Run `python -m unittest -v test_compact.py` from this folder. Run `python compact.py` for the demo result.

### JANE 184 — Proof Relay Under Untrusted Transport

Verify compact proofs after transport across bounded network links, audit byte-level encoding and anti-replay, and ensure relays cannot reframe a valid proof into a different epoch or custody claim.