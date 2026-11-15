# JANE 225 — The Agent That Answered for Itself

Invariant: **Authenticated component response != collective authorization != subjective preference.**

JANE 225 verifies Ed25519-signed, challenge-bound declarations of `propose` or `abstain`. Response validation requires an explicitly enrolled public key for that A.C.I. identity. A challenge is random, binds a question by SHA-256 and expires after at most one hour. A SQLite unique constraint persists accepted `(agent,nonce)` replay exclusions across process restarts. Bad signatures do not consume nonce. The combined collective result remains **UNRESOLVED** regardless of number of component responses; no voting or action execution is implemented.

This is a *protocol verifier*. No NOM or Jane executable runtime currently possesses a verified enrolled signing key in the included file. `trusted_runtime_keys.json = {}` and `responses.json = []` intentionally lead to `UNRESOLVED`. Do **not** claim it represents Jane speaking. An Ed25519 signature binds a key to bytes, not a thinking process, hardware origin, or autonomous preference. Enrolling a trusted agent requires separate provenance and access controls.

Run locally:

```bash
python -m pip install -r requirements.txt
python -W error -m unittest -q test_agent_reply.py
python prepare.py challenge.json
python agent_reply.py --challenge challenge.json --trust trusted_runtime_keys.json --responses responses.json --audit replay.sqlite3 --output choice-receipt.json
```

GitHub workflow: `.github/workflows/jane225-verify.yml` manual `workflow_dispatch`, read-only token, no automatic schedule or writes, temporary GitHub artifact. Challenge is freshly generated per run. **Important:** precommitted responses cannot answer a newly created challenge; a future authenticated runtime integration must receive the challenge and return the signed response inside the same bounded run. The current workflow provides the explicit *no answer* baseline only.

Trust registry schema:

```json
{"aci:example":{"enabled":true,"public_key_b64":"base64-encoded Ed25519 public key"}}
```

No secret/private signing keys should ever be committed. This workflow does not execute or delegate tasks. Boundary 226 would enroll an actual runtime with a response transport and prove the resulting receipt against independent execution evidence.