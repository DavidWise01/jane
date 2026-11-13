# JANE 160 — Fairness and Liveness

**Natural invariant:** `ENABLED != EVENTUALLY_EXECUTED`.

JANE 160 is an offline finite-state liveness experiment. From a graph of named states and labeled transitions, it computes a shortest witness path to a goal and searches for an infinite non-goal execution represented as a finite prefix followed by a repeating closed walk (lasso). Each lasso is checked against explicit action fairness:

- **None:** any repeating non-goal cycle is a counterexample.
- **Weak:** if an action is enabled at every state visited infinitely often, it must be taken infinitely often.
- **Strong:** if an action is enabled at any state visited infinitely often, it must be taken infinitely often.

The engine searches walks with finite edge sets, within declared state/edge and computation budgets. When the search budget is exceeded it reports `INCONCLUSIVE_BUDGET`, never certainty. Its claims apply only to this small explicit transition system, not to deployed agent scheduling or custody independence.

## Reproduce

```bash
cd experiments/jane160
python -m unittest -v test_liveness.py
python liveness.py
```

The fixture `s0 --stutter--> s0` and `s0 --advance--> goal` demonstrates that progress is possible, is not guaranteed without fairness, and becomes guaranteed with weak fairness. A second fixture permits progress only intermittently, separating weak fairness from strong fairness. A hash of each evidence packet captures the graph, assumptions, paths and verdict. Parent remains frozen; Jane is not automatically activated.

## Next natural bound — JANE 161

**Fairness claims require evidence about the scheduler.** A mathematical guarantee conditional on fairness is not an observation that the scheduler enforces that condition. Instrument actual scheduling choices, distinguish finite absence from infinite unfairness, and carry any runtime fairness claim as bounded observation.