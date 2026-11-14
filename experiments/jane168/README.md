# JANE 168 — The Clock That Drifts

**Natural invariant 168:** A clock calibrated at `t0` is not calibrated forever. Its uncertainty grows at a declared bound, and verified anomalies cannot silently reset the trusted baseline.

`drift.py` implements integer millisecond observations, a drift envelope `U(t) = U0 + ceil(elapsed_ms * ppm / 1_000_000)`, expiry by maximum age/uncertainty, conservative jump detection using both observation uncertainties, and an append-only hash-linked local ledger. `test_drift.py` contains 46 tests, all passed locally. `result.json` is the executed deterministic fixture packet. `index.html` is a standalone Canvas2D visualization.

The fixture's configured parameters are 100 ppm drift, 30,000 ms maximum age, 12 ms maximum uncertainty, 3 ms jump tolerance. It distinguishes normal offset (+1 ms at 10 s), clock jump (+50 ms), and age expiry (40 s). **No claim that 100 ppm describes a real clock.** Fixtures are neither physically calibrated nor signed in this experiment; the `evidence_hash` only binds a local identifier. Authenticity checks from JANE 167 are not composed into JANE 168 yet.

A local hash chain does not detect clean suffix truncation unless its head is separately retained; `audit(external_head)` supports comparing to a supplied head. Current trusted parent remains frozen. No autonomous Jane activation, learned promotion, or independent witness certification.

Run: `cd experiments/jane168 && python -m unittest -q test_drift.py && python drift.py`.

## Next natural bound — JANE 169
**Clock drift under changing conditions:** A constant ppm envelope can fail when temperature, power state, network sync, or hardware mode changes. Preserve condition provenance and use interval-based rate bounds without inventing physical independence.