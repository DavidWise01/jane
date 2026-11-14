# JANE 203 — The Summary That Was Queried Adaptively

**Invariant:** A safe-looking individual disclosure does not imply a safe sequence of disclosures. `Safe Individual Query != Safe Query Sequence`.

`disclosure.py` is a deterministic local demonstration of append-only evaluation tracking. It records queried subset identifiers, models, normalized scores, overlap with prior subsets, repeated queries, explicit feedback-based adaptations, and final-test sealing. SQLite transactions enforce a **cumulative policy-credit budget**; denied queries do not enter the log. The SHA-256-linked local ledger is verified before each append, including across process restarts.

**Critical limitation:** The integer credits (base 2, overlap 1 per repeated case, repeated-subset surcharge 2) are illustrative **policy accounting** only, not an information-theoretic leakage estimate, differential privacy ε, statistical validity guarantee, nor a guarantee that any holdout remains secret. Disclosure tracking cannot discover unlogged pathways. An observer with database write access could rewrite the entire unsigned ledger.

## Fixture

Eight holdout IDs; query 1 has cost 2; overlapping query 2 cost 4; an adaptive model follows the two scores; repeat subset query 3 would cost 7 and exceed the 12-credit cap (6+7). Verdict `ADAPTIVE_DISCLOSURE_RECORDED`, denied `CUMULATIVE_BUDGET_EXCEEDED`.

## Run

```sh
python -W error -m unittest -q test_disclosure.py
python disclosure.py > result.json
```

Open `index.html` for an interactive Canvas2D orange-chrome timeline and query-budget simulator. All names, outcomes, and provenance are synthetic; Jane's active parent is unchanged. Review only; no automatic model activation.

## Next natural bound

**JANE 204 — The Queries That Collude.** Separately budgeted analysts can combine aggregate answers, so per-identity budgets alone cannot establish a global release limit. Preserve shared ancestry, cross-client overlap, and a shared sealing boundary.