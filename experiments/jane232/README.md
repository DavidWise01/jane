# JANE 232 — The Custodian Who Shared the Secret

**Invariant:** `Authorized Delegation != Exclusive Custody of a Private Key`.

This increment audits an append-only *signed claim* chain of key custody events. It does not assert that a private key cannot have been copied, prove hardware exclusivity, or independently establish that the public-key enrollment controls are trustworthy. Trust anchors are externally configured and must be authenticated by a separate channel. Different declared root names are not proof of different owners.

## Rules

- Every event is signed with Ed25519 against a pinned public key, has a fresh challenge binding, and belongs to the intended subject.
- Events are canonical JSON, strictly ordered, SHA-256 chained, nonreplaying and limited to 256 per scan.
- Roles constrain event types: registrar enrolls, revokes, rotates; audit signer attests custody; security operator or auditor reports suspected/confirmed exposure.
- Once exposure is reported, further attestation does not restore trust in that key. A new key is required to rotate away from the known compromised material. A rotated key requires new custody attestations.
- Two declared distinct attestor roots are required to report `SIGNED_CUSTODY_CLAIMS_CONSISTENT_NOT_PROVEN`; this is **still not proof of independent people or exclusive custody**.
- Missing evidence remains `NO_CUSTODY_EVIDENCE`. The system executes no requested action; Jane's choice is unresolved.

## Run

```bash
python -m pip install -r requirements.txt
python -m unittest -v test_custody.py
python custody.py --bundle empty-bundle.json --now 2026-11-15T20:00:00Z --output result.json
```

Only pre-established public keys should go into a real enrollment trust registry. Do not commit private keys, access tokens, or secrets. The test suite generates disposable ephemeral fixture keys in process. This is a local offline verification, not an attestation of actual independent custody or live agent execution.