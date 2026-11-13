# JANE 147 — Portable Custody Proof

**Natural invariant:** A signed enrollment is not externally verified custody.

Canonical FLAY coordinate:

```
{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ parent / child }}
```

The `portable.py` module implements canonical JSON statements, operator Ed25519 signatures, two pinned attestor signatures with different *declared* administrative roots, verifier-generated challenge binding, endpoint binding, Chronos UTC-offset validation, replay protection across SQLite restarts, independently supplied checkpoint comparison, and fork/equivocation detection. The verification result is an evidence packet: it never activates or retrains Jane.

## Run locally

```sh
python -m pip install cryptography
python -m unittest discover -s . -p 'test_*.py' -v
python portable.py
```

The full **36/36 tests passed** locally on the same engine and tests published to GitHub. The synthetic demonstration accepts a bundle once and rejects the repeat as `REPLAY`.

## Boundaries

- `https://witness.example.invalid/...` is intentionally **not a deployed endpoint**. This offline test does not fetch any live host, verify TLS/DNS identity, prove separate ownership, or establish independent organizational custody.
- Pinned keys and administrative roots are configured locally as fixture inputs. An operator cannot gain extra attestations just by duplicating keys or relabeling an attestor in a received bundle; but the config itself is not a proof of independence.
- The checkpoint anchor is supplied separately from the bundle, but **the fixture is not published to an actual external append-only service**.
- SQLite stores challenge replay state and observed heads; its own history still needs trusted external anchoring to withstand local privileged rollback. This prototype audits in-process decisions, not a restart-persistent event chain.
- Chronos contains time and angle; the time is signed, not securely clock-attested. `{{ degrees.arcminutes.arcseconds }}` is one angular value, not a complete spatial reference. The nine FLAY anchor positions remain available for nested addresses.
- GitHub and `0root.ai` remain one owned ancestry, not two votes.

## Next natural bound — JANE 148

Fetch real public proofs from independently configured operator endpoints with bounded, allowlisted HTTP, require pinned TLS/key identity and cache immutable snapshots; test service outage and conflicting publications without granting fetch content instructional authority.