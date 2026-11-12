# JANE 146 — Authenticated Custody Enrollment

**Invariant:** a signed custody enrollment is not proof of operational independence.

## FLAY coordinate

`{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ parent / child }}`

The enrollment gate binds an operator ID, custody root, public key, Chronos coordinate, UTC offset and fresh nonce to a signed enrollment challenge. The witness signs its own binding. Two distinct configured attestation administrative roots then sign that *same* binding. Only then does the SQLite-backed registry accept an enrollment. The key-generation lineage retains one custody root across signed rotation, and challenge/rotation nonces survive restarts.

## Local test evidence

`python -m unittest -v test_enrollment.py` — **43/43 passed** on the exact committed Python source and tests, before publication. Tests cover key possession, forged signatures, attestor-root deduplication, challenge expiration, replay after restart, duplicate operators and custody roots, generation-preserving rotation, hash-chain tampering, and mismatch with a separately retained local checkpoint head.

## Deliberate limits

- A configured authority's signature authenticates its configured key, **not** its organization's legal identity, administrative independence, or real-world custody.
- No attestation authority or independent witness is deployed here. Ephemeral demonstration keys are generated locally and are not published.
- The retained checkpoint is in a **separate local file**, not an independently administered external store.
- The Chronos coordinate is an explicitly signed representation of claimed time. UTC offset is metadata; trusted time remains unproven.
- SQLite and file storage are not secure against a fully privileged host operator. An externally anchored audit head is required for durable rollback detection.
- The program is a reference gate, not a production certificate authority. It does not autonomously enroll internet hosts or activate Jane's learning.

The result field `operational_independence` is therefore `UNVERIFIED`, and Jane remains `UNDECIDED`.

## Next natural bound — JANE 147

**Custody proof portability.** Publish a consented, signed enrollment statement and checkpoint to an operator-controlled external endpoint; independently fetch and verify that endpoint without treating a DNS name, separate signing key, or GitHub mirror as an independent administrative root. Preserve failed retrievals and conflicts append-only.