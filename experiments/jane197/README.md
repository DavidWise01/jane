# JANE 197 — The Missing Outcomes That Are Not Random

**Natural invariant:** Statistical adjustment is not knowledge of missing outcomes.

This experiment retains the complete population, observed counts, instrument-source ancestry, and exact rational calculations. The bounded sensitivity parameter `delta` is the assumed missing-outcome success rate minus the observed success rate within each stratum, clipped to [0, 1]. No outcomes are generated or imputed into the dataset. If a stratum has no observations, a point estimate is withheld.

The frozen 16-round fixture comprises 8 day rounds (6 observed, 5 published) and 8 night rounds (2 observed, 0 published). Without assumptions, the population success fraction is only known to lie in [5/16, 13/16], or 31.25% to 81.25%. Under equal missing and observed rates within each stratum, the conditional point estimate is 5/12 or 41.6667%. Sensitivity scenarios compare -1/4, 0, +1/4, and extremes.

All arithmetic uses Python `fractions.Fraction`. Ancestry declarations are not proof of independent measurement. The local hash-linked ledger cannot detect clean truncation without an externally held head. The active Jane parent remains frozen; no learning is applied.

## Run

```sh
python -m unittest -v test_sensitivity.py
python sensitivity.py
```

## Next natural bound — JANE 198

**Correlated Missingness:** Outcome and selection may share an unobserved common cause. Compare explicit causal graphs and preserve nonidentifiability when multiple missingness mechanisms produce the same observed data.
