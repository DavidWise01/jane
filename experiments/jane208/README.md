# JANE 208 — The Calibration That Drifted

**Invariant:** `Past Calibration != Present Accuracy`.

## Engineering

`drift.py` audits transfer of a noisy binary proxy's declared calibration to a deployment. Exact-rational priors, likelihoods and monitoring rates are used throughout. A conditional posterior is permitted only when **all** declared policy gates pass: sample size, calibration chronology, maximum age, population label, artifact-version binding, calibration ID, a bounded positive-rate gap, and nonzero total likelihood. Otherwise `posterior = null` and a specific withhold verdict is emitted. A canonical SHA-256 digest binds input and policy.

The epoch-day integers and identities are synthetic reports, not independently authenticated evidence. Passing summary-rate checks does not establish equal calibration or concept drift absence. This test is not connected to live Jane, a live beacon, or real sensor telemetry.

## Execute

```sh
python -W error -m unittest -q test_drift.py
python drift.py > result.json
```

## Files

- `drift.py` exact-rational transfer verifier and ten reproducible scenarios
- `test_drift.py` 44 regression tests including validation, age boundaries, source version and malformed records
- `result.json` demonstration results
- `index.html` responsive chrome/teal/orange Canvas2D interactive chronology, no external JavaScript

## Next natural bound: JANE 209 — The Drift Hidden in Subgroups

A population-wide rate can remain constant while a subgroup's calibration degrades. `Matching Aggregate Rate != Stable Subgroup Calibration`.