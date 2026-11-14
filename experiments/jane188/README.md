# JANE 188 — The Inbox That Can Be Fabricated

**Invariant:** Complete signed inbox ≠ proven processing.

The verifier separates (1) receiver-signed acknowledgement, (2) executor-signed attempt and output commitment, and (3) observer-signed effect receipts. Its SQLite ledger preserves verdicts and hash-links the local audit; a separately retained head is still necessary for detection of clean truncation. A local signature proves only control of a configured key.

Statuses include `RECEIPT_ONLY`, `SUCCESS_CLAIM_UNCORROBORATED`, `FAILED_ATTEMPT_PRESERVED`, `EFFECT_CONFLICT`, `INSUFFICIENT_EFFECT_ANCESTRY`, and `CORROBORATED_FIXTURE_EFFECT`.

All keys, observer administrators, observations, inputs and outputs are local fixtures. A corroboration verdict does not establish physical execution, real independence, or honesty of the observer. The fixture's `declared_roots` are declared administrative ancestry only. The active Jane parent remains frozen; no automatic learning occurs.

Run `python -m unittest -v test_processing.py` (36 tests), or `python processing.py` for the deterministic evidence packet.

## Next natural bound — JANE 189
**The Effect That Was Staged:** Bind effect attestations to an independently witnessed challenge and timing sequence so a precomputed result cannot be passed off as a response to an actual processing request.