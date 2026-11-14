# JANE 191 — The Challenge Nobody Could Know

**Natural invariant:** `Signed Disclosure != Proven Unpredictability`.

The bounded commit–witness–reveal protocol uses SHA-256 domain-separated seed commitments, Ed25519-signed task freezes, commitments, witness attestations, and reveal statements. The seed is produced by a cryptographic random generator (`secrets.token_hex(32)`) *in the local fixture*. Two differently declared administrative/upstream witness roots are required; signed claimed chronology and disclosure times must be ordered. SQLite persists consumed challenge commitments over restarts and a hash-linked local decision ledger.

The local fixture tests 25 cases, including tampering, insufficient independent *declared* ancestry, early disclosure reports, missing history, forged signatures, modified seeds, and restart replay.

**Important limitations:** Signed fixture clocks do not prove first physical observation; witnesses are not independently operated; reported non-disclosure cannot establish that the challenge was genuinely unknown to the executor. The protocol only checks *observable cryptographic claims*. A hash-chain's clean truncation is not detectable without an externally retained head. Jane's active parent remains frozen; no automatic learning occurs.

Run: `python -W error -m unittest -v test_witnessed_reveal.py && python witnessed_reveal.py`.

## Next natural bound — JANE 192
**Delayed Public Randomness:** Bind the frozen task to a future independently observable randomness event, then show how predictability, event manipulation, and stale public entropy remain separate risks.
