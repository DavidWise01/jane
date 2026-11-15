# JANE 211 — The Subgroup Discovered After Looking

**Natural invariant 211:** `Significant Selected Subgroup != Validated Discovery`.

## Experiment

A frozen 20-subgroup plan defines a synthetic Bernoulli(1/2) null. Every subgroup is tested, and the selected extreme G08 has 16 successes out of 16. `discovery.py` computes two-sided exact binomial p-values and monotone Holm-adjusted p-values over the complete search family, preserving every tested group. It distinguishes exploratory findings from a separately declared untouched final-validation fixture. The declared validation flag is an assumption, not independently attested secrecy.

Run:

```sh
python -W error -m unittest -q test_discovery.py
python discovery.py > result.json
```

The sample is synthetic, observations are assumed independent Bernoulli under a prespecified point null of 0.5, and the inferred findings do not establish effects in a real population. The tool cannot detect unlogged subgroup searches, compromised holdouts, or shared causal roots simply because provenance labels differ. No automatic model activation.

## Files

- `discovery.py`: exact p-values; frozen family validation; Holm family-wise adjustment; explicit final-test checks
- `test_discovery.py`: 43 deterministic regression tests
- `result.json`: reproducible executed demonstration output
- `index.html`: standalone neon Canvas2D timeline and subgroup chart

## Next natural bound: JANE 212 — The Search That Was Never Logged

Preserving a family of recorded comparisons cannot account for silent exploratory queries outside the ledger. A complete experiment requires independently bounded query provenance, not merely a signed report of disclosed tests.