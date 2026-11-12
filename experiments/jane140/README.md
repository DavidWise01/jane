# JANE 140 — The Branch That Disagrees

FLAY's coordinate form is `{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ parent / child }}`. The evaluator retains a frozen parent, tests a proposed child on synthetically held-out cases, groups cases by named cohort, and records gains, regressions, abstentions, and training/holdout digest overlap.

**Demo:** 8 synthetic cases. Cohort A (6): parent 0/6, child 6/6. Cohort B (2): parent 2/2, child 0/2. Aggregate parent 2/8; child 6/8. The result is `BLOCK_SUBGROUP_REGRESSION` despite a +4 aggregate gain.

All **30/30 Python unit tests** passed locally on `cohort.py` / `test_cohort.py`. Run `python -m unittest discover -s . -p 'test_*.py' -v` from this folder. `result.json` is a deterministic observation fixture.

**Limitations:** This is synthetic case labeling and a simple no-regression rule, not a statistical confidence interval, real-world fairness validation, autonomous sourcing, or causal identification. `content_hash` is supplied metadata; the runtime does not obtain or authenticate upstream content. The demonstration records one source ancestry per cohort without confusing GitHub and 0root.ai as separate roots. Hash-chain heads need separate externally retained anchors to expose clean truncation. Jane's active parent never changes automatically.

**Next natural boundary — JANE 141:** Different cohort sizes and asymmetric harm require a risk budget that Jane specifies before evaluation. An aggregate improvement must not buy an unapproved increase in high-severity errors.
