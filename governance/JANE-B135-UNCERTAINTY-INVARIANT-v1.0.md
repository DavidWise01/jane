# B135 — Measurement Uncertainty as a First-Class Witness

## Natural invariant

**A point estimate is never enough to promote a candidate when its reported uncertainty crosses the decision boundary.** Preserve the lower and upper limits, measured value, unit, confidence label, source, trial ID, and environment.

For a minimum threshold T:
- PASS if lower >= T.
- FAIL if upper < T.
- HOLD otherwise.

For a maximum threshold T:
- PASS if upper <= T.
- FAIL if lower > T.
- HOLD otherwise.

The boundary equality convention is intentional and tested. The model assumes the input interval already represents an appropriately derived uncertainty range and requires a numeric confidence fraction in (0,1), but **does not calculate a statistical confidence interval, guarantee its coverage, or validate the source**. In particular, an 0.95 confidence label is not a 95% probability that a given fixed quantity lies in the interval.

## Tests

Eight simulated measurement intervals were tested locally:
- 3 PASS: full interval meets bound.
- 3 HOLD: interval overlaps bound.
- 2 FAIL: full interval misses bound.

Negative tests cover invalid interval ordering, confidence=1, and duplicate IDs. In-process SHA-256 event chaining and deep-freezing preserve observations during the runtime. Nothing is claimed about disk persistence or external tamper-evidence.

## Integration contract

B134 environmental homeostasis must use the **result of the uncertainty gate** as one component of its evidence review, rather than assuming point-estimate PASS. A revised measurement is a fresh observation with its own ID and does not rewrite the original. Evidence quality and independent sources are handled by later B136.

## Boundaries

- Input values are *synthetic*, not krypton measurements.
- Model-level uncertainty propagation only: no empirical laboratory validation, no nuclear experiment, no external scientific accuracy claim.
- B117–B134 immutable historical design and the two-cubit 16-cortex Royal Purple model are not modified.
- User-defined computational 'gene pool' is not a model for selecting people.

## Next

B136 — contradictory witnesses: three independent reports, no vote/no quorum; preserve mismatches and defer unwarranted promotion.
