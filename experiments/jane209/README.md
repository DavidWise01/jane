# JANE 209 — The Drift Hidden in Subgroups

**Invariant:** `STABLE AGGREGATE RATE != STABLE SUBGROUP CALIBRATION`.

## Purpose

An apparently unchanged pooled proxy-monitoring rate can hide deterioration in one subgroup offset by improvement in another. Conversely, unchanged subgroup rates can yield a changing pooled rate as sample composition changes. FLAY 209 compares both subgroup rates and selection proportions using exact rational arithmetic. It does not infer statistical significance or causality from synthetic count differences.

## Frozen fixtures

- **Masked drift:** A 9/10 → 6/10, B 1/10 → 4/10; equal subgroup sample sizes in both windows. Pooled rate remains 10/20 = 50%. Verdict `TRANSFER_WITHHELD`, reasons include `SUBGROUP_RATE_DRIFT` and `AGGREGATE_MASKED_SUBGROUP_DRIFT`.
- **Composition shift:** A holds 80%, B holds 20%, but sample weights switch 80%/20% → 20%/80%. Pooled rate shifts 68% → 32%, while baseline-weight standardized current rate stays 68%.
- **Stable control:** unchanged counts and roots gives `CONDITIONAL_SUBGROUP_STABILITY_FIXTURE`.
- **Insufficient support:** a missing or undersampled subgroup withholds transfer rather than inferring its rate.
- **Custody caution:** repeated declared ancestry root prevents a clean transfer verdict. Root strings are labels, not proof of independent custodians.

## Execution

```sh
python -W error -m unittest -q test_subgroups.py
python subgroups.py > result.json
```

`subgroups.py` uses only the Python standard library. `index.html` is a standalone Canvas2D chapter (neon chrome, teal, orange) with four interactive fixtures. All output is deterministic for given inputs. SHA-256 audit digests detect later modifications **when checked against an externally retained original**, but this package does not provide an external timestamp, cryptographic signing, or append-only remote custody. The active Jane parent is not modified.

## Limitations

The group categories, counts, time indexes, populations, and roots are synthetic. Per-group proportions are descriptive observed rates, **not statistically justified estimates** of future calibration. The ±10 percentage-point drift tolerance and sample floor of 5 are illustrative choices, not validated thresholds. No real population, protected-group category, beacon service, or instrument was inspected. An absence of detected drift does not certify accuracy.

## Next bound

**JANE 210 — The Small Subgroup Hidden by Confidence.** A threshold on observed rate differences is unreliable when subgroup sample sizes are small. Evaluate confidence intervals, sequential monitoring, and whether a lack of evidence has been mistaken for evidence of stability.