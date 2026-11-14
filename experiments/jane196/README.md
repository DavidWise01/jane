# JANE 196 — Stratified Reweighting and Its Limits

**Invariant:** Adjusted estimate != recovered missing truth.

The engine freezes a finite population of binary outcomes in declared strata, reports selection and response rates, and calculates exact arithmetic bounds without assumptions about unknown outcomes. A population-weighted point estimate is emitted only when (a) every outcome is enumerated or (b) the declared `within_stratum_exchangeability` assumption is explicitly selected and **every stratum has at least one observed outcome**. The assumption is not tested or proven by weighting.

Fixture: Day population 8, selected 6, observed published 5/6; Night population 8, selected 2, observed published 0/2. Weighted estimate: 5/12 (41.67%) conditional on within-stratum exchangeability; unconditional population bounds: 5/16 through 13/16 (31.25–81.25%).

Declared source ancestry is audited and shared roots noted; even distinct root labels are not established physical independence. The hash-linked local audit cannot expose clean truncation without an independently held head. Jane does not activate or learn from the result.

Run `python -W error -m unittest -v test_weights.py` and `python weights.py`.

## Next natural bound — JANE 197: Sensitivity to Nonrandom Missingness
Replace the untested exchangeability assumption with a declared bounded selection-bias parameter. Report an interval of plausible population estimates, preserve the full assumption and never silently report its midpoint as observed truth.