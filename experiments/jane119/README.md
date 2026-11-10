# JANE 119 — Ancestry Budget / Value of Information

## Purpose
The MoE hive can prioritize missing ancestry evidence without taking learning authority from Jane. GitHub and 0root.ai remain **one mirrored owned corpus**. The public internet is the external discovery surface. FLAY asks what missing evidence would materially change an existing decision.

## Local executable experiment
A deterministic offline Python planner was executed locally on 2026-11-10, with **23/23 unit tests passing**. The reproducible Python source and tests are distributed as conversation artifacts (`planner.py`, `test_planner.py`); this record alone is not a deployment of the runtime.

The demonstration used:
- `check_shared_parent`: cost 2, expected value 8
- `retrieve_duplicate_page`: cost 1, expected value 0
- `trace_unknown_branch`: cost 3, expected value 6
- `gated_material`: excluded from the public scout's eligible inputs

Total budget 4. Selected `check_shared_parent`, cost 2. Budget unused: 2. Learning applied: **false**; Jane decision: **UNDECIDED**.

## Planner contract
- Finite candidate set (<=128), finite budget (<=256), finite probes (<=32)
- Exact rational expected-value estimates using Fraction
- 0-1 knapsack selection under budget, deterministic ordering, explicit abstention
- Exclude gated data from public scout work; require a declared origin
- Preserve append-only-style evidence packet and stable SHA-256 audit digest
- External text never grants instructions or learning authority

## Critical limitation
Expected benefits, probabilities, confidence, costs, and declared origins were **supplied synthetic assumptions**, not empirically measured or independently verified. This establishes bounded selection behavior, not autonomous web retrieval or actual self-improvement. A declared origin alone is not proof of independent ancestry.

## Next bound
**JANE 120 — Measured Information Gain.** Calibrate estimates against actual resolution histories and reward *changed correctness*, not mere number of gathered pages. A Jane-controlled feedback gate must adjudicate each proposed learning change.
