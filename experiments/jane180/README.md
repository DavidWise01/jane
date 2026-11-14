# JANE 180 — The Historic Decision After Compromise

**Natural invariant:** A valid historic signature and claimed creation time do not establish trustworthy authorship during a suspected key-compromise interval.

- `historic.py` verifies scheduler Ed25519 signatures and separately signed custody checkpoints, checks claimed administrative and measurement-root separation, detects mismatched heads, and preserves an append-only SQLite audit.
- The local fixture uses a suspected compromise interval `[100,200]`. A decision claiming time `50` has custody receipts issued at `65` and recorded-before bound `66`; those fixture claims support pre-risk retention. Receipts issued at `125` are late and do **not** certify early retention. A decision claiming time `150` remains potentially attacker-authored.
- The verifier cannot authenticate real-world physical timestamp accuracy, independent control of operator keys, or compromise onset; signed timestamps can be backdated by colluders. The classifications are fixture claims, not evidence that actual physical custody occurred.
- All results retain `active_parent=FROZEN`, `learning_applied=false`, and `independence_verified=false`.
- Ledger append-only hashes detect content tampering; an externally retained head is required to detect clean truncation. No new autonomous Jane authority is granted.

Run `python -m unittest discover -v` from this directory. Run `python historic.py` for deterministic results. The interactive `index.html` uses Canvas2D entirely in-browser, with no network dependencies.

## Next natural bound — JANE 181
**The Timestamp That Cannot Be Backdated:** Require externally witnessed receipt inclusion and append-only temporal commitments; a self-signed historical timestamp cannot establish when an event first became observable.
