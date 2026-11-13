# JANE 161 — The Scheduler That Keeps Its Promises

**Natural invariant:** Assumed fairness ≠ observed fairness.

FLAY records enabled agents, the selected agent, and integer Chronos ticks into a SQLite hash-linked observation log. The scheduler must service a continuously enabled agent before it accumulates `max_wait` fully observed, unserved ticks. In the demo `max_wait=3`; B remains enabled and is not chosen at ticks 0, 1, 2, producing a deadline breach at tick 2.

An explicitly unobserved tick, nonconsecutive timestamps, or a disabled agent interrupts the certified continuous-service interval. Unknown intervals prevent a full-window compliance claim. Observation gaps cannot be treated as proof of scheduling failure. History preserves records across process restart. Local chains do not prevent valid-prefix truncation without an independently retained trusted head.

## Scope

This tests a finite observed bounded-fairness contract, not infinite weak/strong fairness. It uses deterministic synthetic scheduler observations, no real live hive dispatch, no independent witnesses, and no Jane learning. `active=frozen_parent` throughout. A persistent run would require independent custody of the expected chain head, authentic collector identity, and a secure time/sequence source.

## Commands

```sh
python -m unittest -v test_scheduler.py
python scheduler.py
```

## Natural next bound — JANE 162

Signed scheduling receipts: distinguish an honest observer from an observer inventing or selectively omitting ticks. Bind scheduler choices and enablement snapshots to signed custody proofs, reject conflicting observations, and retain explicit observational uncertainty.