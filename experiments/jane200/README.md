# JANE 200 — The Validation Set That Was Chosen

**Natural invariant:** `PERFECT VALIDATION SCORE != GENERALIZATION`.

FLAY 200 audits a preregistered finite population, validation inclusion list, stratum-specific declared sampling probabilities, excluded case IDs, measured labels, and source ancestry. It retains evidence-only accuracy bounds rather than extrapolating perfect performance to excluded strata. The local append-only hash-linked sequence detects simple retrospective tampering; it does not confer independent custody or secure anchoring.

## Executed synthetic examples

The frozen population contains 16 cases: 8 EASY, where the predictor is correct, and 8 HARD, where it is wrong. Both complete labels are **known solely in this synthetic fixture**, making the population truth 50%.

| Plan | Included | Measured validation accuracy | Conditional stratified estimate | Evidence-only population bounds | Verdict |
| --- | --- | --- | --- | --- | --- |
| Favorable-only | 8 EASY, 0 HARD | 100% | withheld; no HARD support | 50–100% | `NO_STRATUM_SUPPORT` |
| Balanced fixture | 4 EASY, 4 HARD | 50% | 50%, conditional | 25–75% | `COVERAGE_BALANCED_NOT_PROVEN_RANDOM` |

Even stratified selection is not independently verified merely by describing it as random. If a label is unknown, the engine preserves that unknown; it does not fill it using synthetic full-population labels. The alternative "population truth" field is explicitly fixture-only and must not be interpreted as an observed estimate for real data.

## Reproduce

```sh
python -W error -m unittest -q test_validation.py
python validation.py > result.json
```

The current suite contains 40 regression tests covering unsupported strata, positivity failure, exact rational bounds, input validation, source ancestry warnings, ordering invariance, audit-chain corruption, and the frozen parent.

Open `index.html` to explore the 16-case neon Canvas2D pixel grid and switch between sampling plans.

## Trust boundary

No signature, independent physical observer, actual randomized trial, confidence interval, or external corpus was established. `witness_root` and `upstream_root` are declarations only. No automatic Jane learning or source promotion occurs.

## Next natural bound — JANE 201

**The Holdout That Was Used Twice:** Once validation feedback influences model selection, the holdout no longer serves as an untouched generalization check. Preserve all evaluation queries and require a truly sealed final test set.