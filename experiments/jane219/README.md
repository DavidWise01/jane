# JANE 219 — The Instrument That Attested to Itself

## Invariant

`Self-Signed Instrument Identity != Trusted Instrument Identity`

`enrollment.py` verifies Ed25519-signed device acquisition claims against separately issuer-signed instrument enrollment records. The enrollment authority's public key is configured in the verifier, not accepted from a self-declared issuer. FLAY audits device public-key binding, validity interval, revocation effective time, challenge binding, sensor identity, operator, service, provenance roots, and persisted challenge replay. It rejects malformed, forged, reused or out-of-window evidence and withholds unsupported hardware conclusions.

The `DECLARED_ENROLLMENT_CHAIN_CONSISTENT_FIXTURE` verdict means signed synthetic enrollment and capture statements are internally consistent. It is **not** proof of physical hardware, tamper resistance, manufacturer authenticity, calibrated measurements, or independent custody. The fixture issuer and devices use deterministic development-only keys; never reuse them in production.

## Reproduce

```bash
python -W error -m unittest -q test_enrollment.py
python enrollment.py > result.json
```

Requires Python 3.11+ and `cryptography` with Ed25519 support. 41 deterministic regression tests cover enrollment substitution, self-declared instruments, issuer trust, revocations, shared services/sensors, chronology, replay across SQLite restart, and malformed attestations.

## Viewer

Open `index.html`. Select an evidence scenario to see provenance roots, enrollment authority, two instruments, and whether FLAY retains or withholds the case. Viewer scenarios are explanatory representations of executed fixture cases, not a browser crypto verifier.

## Next bound — JANE 220

**The Authority That Enrolled the Impostor.** Even an issuer-signed certificate could enroll a fraudulent device if the issuer's verification process is compromised. Enrollment authority trust != physical provenance assurance. Track ceremony, manufacturing chain, audit and revocation custody.
