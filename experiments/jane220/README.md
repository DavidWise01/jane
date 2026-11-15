# JANE 220 — The Authority That Enrolled the Impostor

**Natural invariant 220:** `Trusted Enrollment Signature != Genuine Device Provenance`.

An enrollment certificate may have a correct Ed25519 signature while identifying an impostor. This synthetic FLAY audit checks a claimed manufacturer statement, ordered signed custody transfers, a separately signed enrollment, subsequent acquisition, and issuer-signed revocation evidence.

## Evidence gates

1. Verify the challenge and declared acquisition deadline.
2. Verify the pinned manufacturer signature, device public key, manufacturing batch and model.
3. Trace individually signed custody transfers from the manufacturer to the claimed enrolling custodian. Preserve ordering.
4. Verify enrollment signature, enrolled key, validity interval, and consistency with the manufacturing identity.
5. Verify signed revocation status and acquisition signature, challenge nonce, payload commitment, capture chronology and distinct declared sensor/operator/service/root.
6. Store an append-only hash-linked local SQLite verdict and reject repeated nonces across process restarts.

**Limits:** All device keys, custodian names, clocks, and manufacturer authority are deterministic test fixtures. A signed manufacturing assertion does *not* establish true factory production; a signed transfer does *not* establish physical possession. The code has no access to physical instruments, attestation hardware, or an external independent authority. It does not provide general PKI certification, revocation timestamps, a real-time revocation freshness guarantee, or cryptographically complete immutable custody. The SHA-256 SQLite record chain is local tamper evidence, not independent retention. The active Jane parent remains unchanged.

## Reproduce

```bash
python -W error -m unittest -q test_provenance.py
python provenance.py > result.json
```

Open `index.html` for a self-contained neon Canvas2D custody diagram with eleven synthetic scenarios. No CDN or external resources are required.

## Next natural bound — JANE 221

**The Factory That Signed a Fiction:** Even a matching manufacturer record, transfer chain and enrollment can be fabricated by colluding operators. A trusted signature is not an independent observation of manufacture; add independent production evidence, key-birth evidence, provenance transparency, and explicit uncertainty around factory compromise.