# JANE 141 — The Cost of Being Wrong

FLAY address: `{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ parent / child }}`.

**Natural invariant: Improved accuracy does not imply acceptable risk.** The severity-weighted risk budget is declared before evaluating the holdout. It includes an overall ceiling, a ceiling for each cohort, and a separate maximum for newly introduced severe errors. The parent remains frozen and active.

## Deterministic demonstration
Eight synthetic cases: six routine mistakes are corrected, eliminating 12 cost units. Two critical regressions create 100 units (severity 10 × reversibility 5 × 2 mistakes). The critical cohort is budgeted at zero, the overall budget is 12, and no newly severe mistakes are permitted. Result: **BLOCK_NEW_SEVERE_ERRORS**; Jane remains undecided and learning is not applied.

## Tests
**37/37 locally executed tests passed** on `risk.py` and `test_risk.py`. Run `python -m unittest discover -s . -p 'test_*.py' -v` from this directory.

## Boundaries
The risk weights are chosen synthetic values, not calibrated real-world harm. Evidence hashes are supplied as fixture metadata rather than fetched or authenticated. The local append-only hash chain requires an external retained head to detect valid truncation. Chronos is an address field, not trusted clock time. This experiment performs neither real-world causal inference nor automatic learning.

## JANE 142
Estimate upper and lower bounds of risk when labels are missing. Request the highest-value missing observation, rather than treating unknown harm as zero.
