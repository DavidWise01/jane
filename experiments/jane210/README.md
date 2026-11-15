# JANE 210 — The Small Subgroup Hidden by Confidence

**Invariant:** `No significant drift != Evidence of stability`.

FLAY compares binomial baseline/current subgroup proportions and explicitly distinguishes (1) too few samples, (2) uncertainty spanning both meaningful change and equivalence, (3) conditional equivalence, and (4) conditional material drift. All expected subgroups must be present. Declared shared ancestry withholds a favorable verdict. The frozen input is SHA-256 committed with canonical serialization.

## Method and scope

For each proportion use a Wilson-score interval with `z=2.241402727604947`, corresponding to *nominal* 97.5% two-sided coverage per interval. Bonferroni correction is used to target simultaneous 95% coverage across the two constituent intervals; subtract their endpoints to form a conservative interval for current minus baseline. Wilson intervals do **not** guarantee exact coverage for all finite-sample Bernoulli distributions. The demonstration also requires 30 observations in each period and a predeclared ±0.10 equivalence margin. It is not a complete TOST procedure, and no valid generalization follows without a reasonable sampling model. An additional multiple-subgroup correction would be required for family-wise control across many groups.

No real calibration, independently verified physical witness, or active Jane learning is claimed. This is a deterministic synthetic local engine.

## Run

```sh
python -W error -m unittest -q test_equivalence.py
python equivalence.py > result.json
```

Open `index.html` for the neon orange/chrome/teal Canvas2D uncertainty scene.

## Next — JANE 211: The Subgroup Discovered After Looking

If a team searches hundreds of subgroups until one exhibits a striking drift, an uncorrected confidence interval for the chosen subgroup understates selection uncertainty. Preserve the search and adjust the family of tests rather than validating the selected subgroup alone.