# JANE 214 — The Sensor That Was Replayed

**Invariant:** Independent custody does not prove independent *fresh* acquisition.

## Mechanism

FLAY214 verifies Ed25519 signed challenge and signed sensor acquisition reports against an immutable task digest and nonce. It checks challenge issuance and expiration, claimed capture start/end chronology, capture-delay policy, per-sensor boot label and frame index, sensor roots, sensor identities, and matching content-addressed payload digests. Separate signatures alone do not count as separate sensors. A SQLite ledger retains consumed challenge nonces and capture identifiers across verifier restarts, with a locally hash-linked audit trail. Malformed/rejected packets do not consume a nonce.

A valid fixture reports `FRESH_ACQUISITION_FIXTURE`. Replay of the nonce is `REPLAY_CHALLENGE`, reused capture ID with a new nonce is `REPLAY_CAPTURE`, early/late capture is `INVALID_CAPTURE_CHRONOLOGY`, and shared sensor/ancestry is withheld. Other tests check payload disagreement, malformed frame, missing boot, forged signatures, and audit corruption.

## Run

```bash
python -W error -m unittest -q test_acquisition.py
python acquisition.py > result.json
```

Open `index.html` for a responsive high-definition Canvas2D narrative of the verifier's evidence path.

## Boundaries

Every witness, signer, clock, sensor ID, boot ID, frame number and payload in the tests is synthesized. The engine validates *signed claims* of fresh acquisition, not physical access to hardware. A malicious sensor can sign fabricated timestamps or bind stale image data to a new nonce; the replay gate detects only previously recorded challenge/capture IDs. The local audit is not an independent secure witness. Never promote synthetic fixture success to evidence of actual physical acquisition. No automatic Jane learning or active-parent mutation.

## Next natural bound

**JANE 215 — The Frame That Was Re-labeled.** Even unique capture identifiers and a fresh challenge can accompany recycled pixels if the sensor re-encodes stale content. The next experiment tests content similarity, acquisition attestation, and the limits of freshness detection.