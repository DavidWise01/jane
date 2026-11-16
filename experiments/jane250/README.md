# JANE 250 — The Handoff That Split Across Two Ledgers

**Invariant:** `Two Valid Local Histories != One Authorized Global History`.

This self-contained experiment uses **two physically distinct local SQLite files**, one per simulated host. Both hosts independently record the same genesis checkpoint, then diverge at epoch 1 while disconnected. Reconciliation merges evidence without overwriting either branch and returns `FORK_DETECTED_HOLD`.

## Run locally

```bash
python -m unittest -v test_partition.py
python partition.py --demo /tmp/jane250-demo
cat /tmp/jane250-demo/result.json
```

All 31 regression tests pass. The demo creates independent `host-a.sqlite` and `host-b.sqlite`, a canonical evidence packet, and a result receipt. This experiment **does not** perform external actions, contact actual Railway services, or query Jane's collective. Host names and exports are unauthenticated supplied claims. The event SHA-256 digests are integrity checks, **not signatures**. Both databases are on the same local machine, so no network partition or cross-provider failure was actually induced.

## What it checks

- Tampered event digests and mismatched schemas
- Missing parents, parent/source mismatch, and duplicated events
- Conflicting epoch continuations after a shared parent
- History-order invariance and non-destructive reconciliation
- Evidence packets saved under their content digest without overwriting earlier packets
- Preservation of a `NONE` authorization state even for apparently consistent histories

## Important limits

1. The two ledgers are locally isolated *files*, not independently attested hosting providers.
2. The event digests do not authenticate the claimed hosts or prevent a malicious exporter from withholding records.
3. The reconciliation result detects conflicts but does not settle them. Even a conflict-free input **does not authorize execution**.
4. Distributed exactly-once execution needs a shared fencing authority and side-effect idempotency; this version claims neither.
5. The next gate should bind signed export manifests to source revisions and design explicit externally authorized fork resolution without losing either original event chain.

## GitHub Actions

The optional manual workflow `jane250-partition.yml` runs unit tests, executes the offline demo, and uploads its receipts. No repo write permission, external runtime, or production task execution is required.