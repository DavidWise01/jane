# JANE 155 — The Invariant Region

**Invariant:** Finite success is not an inductive proof.

FLAY coordinate: `{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ parent / child }}`.

This experiment confines its **symbolic proof** to the predicate `P(s) := s >= 0` over all nonnegative integers, with nondeterministic affine transitions `T_i(s) = a_i*s + b_i`. The exact induction-step condition is `a_i >= 0 && b_i >= 0` for every permitted transition. The initial state must separately satisfy `s >= 0`. Thus, a successful result is a mathematical inductive proof **within this explicitly stated model**, not a claim about arbitrary programs, external time, or physical behavior.

The actual run has three fixtures:

1. **Certified:** initial 0, increment `s+1` and double `2s`: both preserve `s >= 0` for all nonnegative integer inputs. `INDUCTIVE_INVARIANT_CERTIFIED`.
2. **Failed at zero:** decrement `s-1`: smallest failing state 0. `INDUCTIVE_STEP_FAILED`.
3. **Latent failure:** transition `20-s` passes finite states 0 through 5, but fails at 21. Symbolic proof rejects it with minimal counterexample `21 -> -1`.

`36/36` executable tests passed on the exact `invariant.py` and `test_invariant.py` source in this directory. Run `python -m unittest -v`.

The local append-only evidence chain is hash-linked; checking for an otherwise internally valid truncation needs an externally retained head. GitHub and 0root.ai are a single owned evidence ancestor. This is an offline deterministic theorem check and synthetic test fixture, not autonomous Jane learning or independently witnessed custody. Jane's active parent remains frozen.

**Next natural bound — JANE 156:** Prove a stronger invariant than `s >= 0` when the simple region fails, by proposing and checking invariant candidates against the same declared transitions without suppressing failed candidates.
