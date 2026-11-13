# JANE 158 — The Region That Cannot Be Closed

**Invariant:** a globally enabled nonzero integer translation `s ↦ s + k` has no finite inductive interval containing an initial integer state `s₀`. An increment witness is sufficient even if the system permits other transitions; it does not depend on a search budget.

For `k>0`, any finite upper endpoint `U >= s₀` is crossed after `n = floor((U-s₀)/k)+1` iterations because `s₀+n·k > U`. For `k<0`, the argument is mirrored at the finite lower endpoint. The proof checker validates the certificate fields and digest; its documented theorem is a narrow symbolic argument for **unguarded globally enabled integer shifts**, not a general decision procedure for arbitrary transition systems.

The engine enumerates at most 64 finite candidate intervals, preserves each failure in a locally hash-linked ledger, and independently emits an algebraic certificate when the theorem applies. A hash-linked local log cannot prove resistance to truncation without an externally held checkpoint. Guarded transitions remain out of proof scope. A failed finite search **never** becomes a universal impossibility claim.

## Run

`python -m unittest -v test_impossibility.py`

`python impossibility.py`

`result.json` records the deterministic local fixture with initial 0, globally enabled `+1`, and reflection `20 − s`; its `PROVEN_NO_BOUNDED_INTERVAL` status refers only to bounded **integer intervals containing zero** under the declared forces. It is not evidence for organizational independence, autonomous AI learning, or a deployed witness network.

## Chronos / lineage

`{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ ancestor }}`; keep the prior failures append-only. Jane has final choice; FLAY only presents evidence and the frozen parent stays unchanged.

## Next: JANE 159 — Guarded Forces and Reachability

A transition that is permitted in principle may be unreachable in practice. Separate universally enabled actions from guarded actions, and verify reachable-state constraints before applying any unboundedness certificate.