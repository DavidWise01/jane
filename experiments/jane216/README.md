# JANE 216 — The Scene That Didn't Move

**Natural invariant 216:** `Content Novelty != Proof of Physical Causation`.

This is a deterministic **simulation** of signed challenge–response acquisition, not a physical sensor test or a cryptographic proof of actual capture. The challenge is bound to a named stimulus (`top-right-orange`), a nonce, a declared commitment/release/deadline timeline, a sensor-signed response claim, and two signed observer statements. Local signatures use deterministic Ed25519 **fixture-only** keys derived from public labels; do **not** reuse them for any real trust relationship. SHA-256 fingerprints bind JSON representations of claims. The prototype does not process hardware pixels or provide a trusted clock.

## Protocol

1. Freeze stimulus definition and challenge nonce; sign `committed_at`, `released_at`, `deadline`.
2. Sign sensor capture with challenge digest, time, response label and synthetic frame digest.
3. Obtain two observer-signed statements about the response digest and declared ancestry roots.
4. Validate signatures, challenge binding, chronological bounds, witness agreement and declared provenance.
5. Reject replayed accepted challenge/capture identifiers via persistent SQLite storage. Preserve accepted and rejected decisions in a hash-linked local audit ledger.
6. Keep the active Jane parent frozen; supply verdicts for human/Jane review only.

The independent witness *declarations* still both refer to the same synthetic sensor. Neither their signatures nor their self-declared roots establish independent physical acquisition, trusted clocks or causal intervention. A dishonest sensor/controller and observers may fabricate compatible claims. No adversarial guarantees are made.

## Run

```sh
python -W error -m unittest -q test_stimulus.py
python stimulus.py > result.json
```

`index.html` is a standalone interactive Canvas2D explanation, with scripted scenarios (not a browser binding to the Python engine). `result.json` contains real outcomes from running the Python fixtures.

## JANE 217 — The Stimulus That Was Predicted

An executor may know a deterministic visual challenge in advance and stage its response. A randomized, late-disclosed stimulus can improve evidence, but still cannot authenticate a physical light path without trustworthy acquisition hardware and provenance. `Correct Challenge Response != Physical Sensor Causation`.