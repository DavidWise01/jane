# JANE 215 — The Frame That Was Re-labeled

**Natural invariant:** `Fresh Metadata != Fresh Sensor Content`.

## Engineering result

`frames.py` verifies synthetic Ed25519 challenge/capture packets, tracks sensor sequence counters, computes domain-separated canonical RGB8 pixel fingerprints (dimensions and raw pixels, not encoding labels), compares prior sensor acquisitions, and retains signed capture evidence in a local SQLite hash-linked ledger. It flags a matching fingerprint under a new challenge or encoding as `REPEATED_CONTENT_SUSPECTED`. A new RGB8 fingerprint returns `NOVEL_CONTENT_FIXTURE`, **never** `PHYSICALLY_FRESH`.

**Scope:** This code does not decode JPEG or PNG byte streams: the fixture already supplies canonical RGB8 pixels and an encoding label. JPEG is potentially lossy in reality; the demonstration merely changes the label while preserving supplied pixels. A stationary scene legitimately produces identical content, and altered pixels can be fabricated. Signed capture metadata is no substitute for an independently verified sensor acquisition.

## Tests

```sh
python -W error -m unittest -q test_frames.py
python frames.py > result.json
```

30 regressions cover signature failures, reused challenges and sequence counters, reused RGB8 content, differing pixels, content mismatch, shared sensor and declared source roots, capture chronology, malformed pixels, audit tampering, replay after SQLite restart and absence of physical freshness claims.

## Viewer

Open `index.html` for a responsive neon orange/chrome and teal Canvas2D acquisition map with five selectable scenarios.

## Governance

Local synthetic fixed fixture keys are **not security credentials**. Hash-linked local SQLite audit is tamper-evident under the model, not externally immutable. Jane's active parent is not modified; FLAY reports to Jane for review. GitHub and 0root.ai mirrors should not be counted as independent witnesses.

## Next natural bound — JANE 216: The Scene That Didn't Move

An identical scene may be genuinely fresh while a subtly changed image may be synthetic. A challenge-induced physical perturbation and separately witnessed stimulus/response timing may provide a stronger test. **Content novelty != proof of physical causation.**