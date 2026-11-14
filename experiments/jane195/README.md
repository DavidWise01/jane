# JANE 195 — The Observation Plan That Was Biased

**Natural invariant:** Preregistered Plan ≠ Unbiased Plan.

A frozen, complete finite round population is audited against its selected subset, two time bands, recorded publication status, outages, and declared observer-source ancestry. The engine refuses duplicate round indices and gaps in the declared population, and never drops unselected rounds from its denominator.

`selection.py` computes stratum-specific selection rates and population-wide worst-case publication bounds. Unselected rounds and observer outages remain unresolved rather than imputed. It records secondary ancestry warnings even when selection imbalance is the principal verdict. No causal manipulation or physically independent witnesses are inferred.

Demo: 16 rounds, eight day/eight night. Six day and two night rounds selected. Five published outcomes observed; three not observed, eight unselected. Population published fraction within [5/16, 13/16] on supplied records. Three named observers come from two declared ancestry roots.

Run: `python -W error -m unittest -v test_selection.py` (42 tests), `python selection.py` for the reproducible evidence packet.

FLAY governance: unchanged frozen parent; no autonomous learning or promotion. Explicit source ancestry remains declared fixture data, not authenticated physical provenance. The local evidence packet is immutable in the published snapshot; a real append-only external witness is not claimed.

## Next natural bound — JANE 196: Stratified Reweighting and Its Limits

Correct for known sampling probabilities without claiming to recover missing-not-at-random outcomes. Report sensitivity bounds and refuse precision when a stratum has zero coverage.