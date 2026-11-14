# JANE 190 — The Executor That Predicts the Challenge

**Invariant:** A fresh nonce is not necessarily an unpredictable challenge.

The JANE 190 fixture freezes a task commitment before nonce generation, signs the challenge and its disclosure event, and checks that the executor and effect reports refer to that exact challenge. FLAY rejects stated early leaks, forged signatures, nonces, mismatched inputs, and chronologically inconsistent claims. Successful receipts are retained in a SQLite replay ledger with a hash-linked event audit. Previously seen nonces remain invalid after restart.

**Boundary:** Signed timestamps and declared disclosure chronology are claims. The software cannot prove nonce secrecy or rule out an *undisclosed* early leak; neither physical execution nor independent observation is proven. Root names and keys are synthetic fixtures. This gate should fail closed when independently authenticated generation/disclosure evidence is unavailable. The historic parent is frozen; no learning or activation takes place.

Run `python -W error -m unittest -v test_challenge.py` (30 tests), followed by `python challenge.py`.

## Next natural bound — JANE 191
Challenge generation should produce an independently checkable commitment to the *sequence*: freeze task; commit seed; disclose unpredictable nonce after freeze; bind attested execution to challenge; separately retain inclusion evidence. Explore trusted randomness and independent challenge-generation roots rather than interpreting signed self-reports as proof of secrecy.