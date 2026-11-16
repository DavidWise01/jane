# JANE 251 — The Witness That Chose a Fork

**Invariant:** `Detected Conflict != Authorized Conflict Resolution`.

A fail-closed, *locally tested* three-signer reconciliation gate for the simulated JANE 250 two-host fork. Both complete source histories are retained and committed by SHA-256. The challenger names the exact fork, and three Ed25519 votes sign the challenge and fork digest. Unanimous `KEEP_A` or `KEEP_B` produces a **signed-claims-consistent receipt**; disagreement, abstention, forgery, a different history, missing signers, expired challenge, or conflicting root declarations produce `HOLD`. Every result has `authorized_execution: false`.

**Important:** The JSON registry shipped in the same bundle is NOT independently trusted. All witnesses, controller names, and platforms are synthetic fixtures. A malicious submitter could generate three signatures and three names. The code therefore explicitly refuses to call the result independently authorized. The SQLite uniqueness guard works within one database and is not a cross-provider fencing authority.

## Run

```bash
python -m pip install -r requirements.txt
python -m unittest -v test_resolution.py
python resolution.py unanimous-fixture.json --out /tmp/jane251-unanimous.json
python resolution.py disagreement-fixture.json --out /tmp/jane251-disagreement.json
```

`python make_fixtures.py` regenerates synthetic witnesses (and will overwrite fixture receipts). No private signing keys are committed, and no live agent is contacted. The static fixture's challenge expires the day after its generation; regenerate for current-time verification.

## Next gate

Trust anchors must be enrolled **outside** the untrusted bundle, independently verified against an executing process, and bound to a real shared fencing authority before any cross-provider continuation or side effect. Keep both fork branches append-only and save the signed resolution separately.

## GitHub workflow

The manual `jane251-resolution.yml` workflow runs the unit tests, regenerates short-lived fixtures, verifies agreement/hold cases, and uploads receipts. Read-only permissions; does not resume agents or modify GitHub/Railway state.