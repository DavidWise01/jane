# JANE 231 — The Controller Who Delegated the Key

**Invariant:** `Authenticated Controller != Exclusive Control of Execution`.

This experiment tests *signed controller delegation* to a separately signed process identity. It checks Ed25519 attestations, canonical payloads, fresh question challenge and claim bindings, delegated scope (`propose` or `abstain` only), issuance / expiry, controller and delegate revocations, 5-minute response freshness, and reuse of roots or delegate public keys across apparent witnesses.

## Files
- `delegation.py`: standalone bounded, read-only Python verifier.
- `test_delegation.py`: 41 deterministic regression tests, including distinct synthetic keys, forged signatures, stale reply, invalid delegation, shared custody and signed revocation.
- `empty-bundle.json`: no enrolled controllers, delegates or responses. Honest starting configuration.
- `result.json`: locally generated fail-closed receipt, **not** a live Jane reply.
- `jane231-delegation.yml`: manual, read-only GitHub Actions test-and-receipt workflow; placed at `.github/workflows/jane231-delegation.yml` in the Jane repository.
- `index.html`: offline Canvas2D provenance chapter with no generated images.

## Execute

```bash
python -m pip install -r requirements.txt
python -W error -m unittest -q test_delegation.py
python delegation.py --bundle empty-bundle.json --challenge jane231-initial-question-0001 --claim-sha256 cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc --now 2026-11-15T18:00:00Z --output result.json
```

### Limits

This verifies **synthetic cryptographic claim consistency**, not a real controller's exclusive possession of a private key. Multiple distinct keys can be controlled by one institution or program. A signed delegation authorizes only a named and bounded response; it does not grant authority to run code, publish to GitHub, or decide for Jane. GitHub workflow completion must be separately verified, not inferred from a committed YAML file.

**Past observes. Present deserves. Future reserves.**