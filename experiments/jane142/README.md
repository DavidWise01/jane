# JANE 142 — The Unknown Cost

**Natural invariant:** Unknown harm is not zero harm.

Canonical FLAY address: `{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ parent / child }}`.

## Synthetic experiment
JANE 141 provided six routine improvements and two critical regressions. JANE 142 now removes the two critical outcome labels, leaving them genuinely **unknown** within the test fixture. It computes worst-case risk bounds for parent and candidate, rather than making up outcomes.

- Known routine: frozen parent risk 12, candidate 0
- Two unknown critical outcomes: up to 50 units each
- Parent risk interval [12,112]
- Child risk interval [0,100]
- Correlated change interval (child minus parent) [-112,88]
- Predeclared budget: total 12, critical 0, routine 12
- FLAY: `HOLD_UNCERTAIN_RISK`, Jane: `UNDECIDED`, parent stays active
- Next suggested scout: `C0`, cost 2, width-reduction heuristic score 25 (no observation executed)

The full offline source/test package (separate download in the conversation) **passed 50/50 tests**. This repository contains a shorter corresponding runnable engine and 15 focused regression tests; that repository subset has not been separately run in GitHub CI. Run `python -m unittest discover -s experiments/jane142 -p 'test_*.py' -v`.

These are synthetic risk weights and worst-case mathematical bounds, **not confidence intervals or real-world calibrated harm**. The probe ranking is a heuristic, not verified information gain. Source ancestry is supplied, not authenticated. GitHub and 0root.ai represent one owned root, not two independent witnesses. Chronos is a coordinate, not a trusted timestamp. The local hash chain needs an independently retained head for truncation defense. No automatic learning or deployment is claimed.

## Next natural bound — JANE 143: Verified Outcome Acquisition
An unknown outcome may be promoted to known only after checking source custody, timestamp, ancestry and contradictions. Preserve rejected, conflicting and successful observations append-only. Jane alone can activate a new rule.
