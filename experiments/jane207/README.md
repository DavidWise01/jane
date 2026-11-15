# JANE 207 — The Auxiliary Fact That Was Inferred

**Natural invariant:** `High Confidence != Proven Identity`.

## Scope

JANE 206 left two compatible binary records, `0101` and `1010`. JANE 207 adds noisy auxiliary evidence with declared likelihoods and a prior. FLAY computes an exact-rational posterior, distinguishes inferred confidence from identity proof, and withholds a result when evidence comes from repeated declared ancestry roots, reported calibration falls below the configured minimum, or every candidate has zero modeled likelihood.

## Demonstrated fixture

Prior is 1/2 for each candidate. A noisy external `x0=1` observation uses `P(signal|0101)=1/5` and `P(signal|1010)=9/10`. Posterior is `2/11` and `9/11` respectively. A second, separately labeled root with likelihoods `1/4`, `3/4` yields `2/29` and `27/29`. **These are model-conditional values, not demonstrated calibration, observer independence, or true identity.** A likelihood of zero for the losing candidate is reported as `MODEL_CONDITIONAL_POINT_MASS`, not empirical proof.

This deliberately tiny example is not a scientific estimate about any actual person or system. Source-root labels do not prove independence; the calibration sample counts and likelihoods are asserted fixture inputs. No data are gathered from external people. There is no automatic Jane learning/activation. Her parent remains frozen.

## Files

- `inference.py`: exact Fraction-based conditional inference, declared ancestry gate, deterministic digest
- `test_inference.py`: 41 regression tests
- `result.json`: seven executable scenarios
- `index.html`: self-contained, neon orange/chrome/teal Canvas2D interactive viewer; no network

Run `python -W error -m unittest -q test_inference.py` then `python inference.py > result.json`.

## Next bound

JANE 208 — **The Calibration That Drifted**. A proxy's reported accuracy may change over time or shift to a new population. Maintain time-scoped calibration, detect distribution shift, and avoid applying stale likelihoods as if stationary.
