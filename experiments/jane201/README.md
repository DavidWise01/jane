# JANE 201 — The Holdout That Was Used Twice

**Invariant:** Holdout reuse does not constitute independent validation.

## Scope

`holdout.py` stores deterministic append-only local events for dataset freezing, model evaluation, score disclosure, model selection, final-set sealing, and one final evaluation. FLAY201 distinguishes development-set reuse from final-test exposure, checks member-hash intersection, and returns explicit withholding reasons for early leakage, repeat testing, or model adaptation after final feedback.

A hash-linked local event chain preserves declared event order but does **not** independently prove that private score access did not occur, that case identifiers represent genuinely disjoint data, or that timestamps/people were independently witnessed. The **sealed** outcome is `SEALED_FINAL_FIXTURE`, not proof of real-world test isolation. No automatic learning or parent mutation.

## Run

```bash
python -W error -m unittest -q test_holdout.py
python holdout.py > result.json
```

The file `index.html` is a standalone animated neon Canvas2D chronology viewer with scenarios sealed, leaked, repeated final evaluation, and model adaptation after final feedback.

## Engineering constraints

- Exact JSON canonicalization and SHA-256 linked event history
- All evaluations and score disclosures retained, no deletion
- Final evaluation withheld if pre-seal exposure, repeated final evaluation, overlapping declared members, or adaptation after final disclosure
- A reused development set is explicitly marked, even where the final test remains sealed
- Distinct names alone are not proof of independent source ancestry or physical data separation

## Next natural bound

**JANE 202 — The Test That Leaked Through a Summary.** A model can receive test-set information through aggregate metrics, benchmark tuning, shared embeddings, or third-party summaries without direct raw test access. The next experiment will track information-flow ancestry across indirect disclosures.