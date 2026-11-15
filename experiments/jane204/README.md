# JANE 204 — The Queries That Collude

**Natural invariant:** `Independent Query Budgets != Independent Information`.

## Experiment

Three synthetic agents (ADA, BERT, CLIO) issue disclosures derived from one sealed holdout. A collector merges overlapping query subsets. Each disclosure event retains the dataset-root ancestry, submitting agent, recipient, subset, payload hash, event identifier and illustrative credit cost.

FLAY applies three *simultaneous* limits: global holdout credits (12), per-agent credits (8), and per-recipient credits (8). A recipient change does not reset the global limit. Every attempted release is validated inside one SQLite transaction; rejected releases do not mutate the log. Repeated outputs remain chargeable rather than silently free.

### Executed fixture

1. ADA releases records `[0,1,2]` to COLLECTOR for 4 credits.
2. BERT releases records `[2,3,4]` to COLLECTOR for 4 credits. Their union contains five record indices and both claims share the holdout-204 ancestry root.
3. CLIO's +1 COLLECTOR release fails (`RECIPIENT_BUDGET_EXCEEDED`).
4. CLIO's +3 release to OTHER succeeds, taking global spend to 11/12.
5. BERT's +2 release to OTHER fails (`GLOBAL_BUDGET_EXCEEDED`).

## Validation

```sh
python -W error -m unittest -q test_collusion.py
python collusion.py > result.json
```

42 Python `unittest` checks cover source ancestry, cross-agent recipient union, global budget enforcement, per-agent and per-recipient limits, atomic rejection, exact cap boundaries, deterministic digests, replay after restart, and tampering with the local hash-linked audit.

Open `index.html` for the interactive Canvas2D neon mesh, switching among cross-agent merge, recipient block, global block, and shared ancestry.

### Evidence limits

The engine is a **local synthetic policy fixture**. Credits are illustrative policy units, *not* differential privacy epsilon, a guarantee against reconstruction, quantified mutual information, or real bits leaked. An agent can communicate outside a ledger; separate keys are not necessarily independent actors; local SHA-256 links are not externally witnessed or immutable against administrator replacement. There are no actual holdout samples or independently authenticated agents, and **no automatic Jane learning or activation**. The frozen parent remains unchanged.

## Next natural bound — JANE 205

**The Reconstruction That Was Smaller Than Its Parts.** Combined subset summaries can reveal specific individual holdout labels even when cumulative policy credits remain under a threshold. Build explicit linear-query rank/reconstruction tests and an inference-risk gate; neither budget compliance nor partial-query overlap alone proves confidentiality.