# JANE 152 — The Noncommuting Histories

**Natural invariant:** A∘B ≠ B∘A in general. A two-parent merge references both histories but does not prove that executing both event sequences produces the same valid state.

FLAY address: `{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ parent / child }}`.

## Executed local experiment

- Shared immutable ancestor: `count = 2`.
- Branch A: `add count 3`. Branch B: `multiply count 2`.
- A→B gives 10; B→A gives 7; status `NONCOMMUTING_BRANCHES`.
- A disjoint-field update gives identical states; status `COMPATIBLE_CONTINUATION_CANDIDATE`.
- A precondition can make one ordering invalid; status `ORDER_DEPENDENT_FAILURE`.
- The entire event payload for both branches, both execution traces, both terminal states, canonical digest, Chronos, and one source ancestry are preserved.
- Jane's active rule stays `frozen_parent`. No autonomous learning.

All **40/40 unit tests passed locally** against the exact source in this directory. Reproduce: `python -m unittest -v test_commute`.

## Limits

Operations are a small synthetic deterministic DSL (`set`, `add`, `multiply`, `delete`, `require`, `set_if_absent`) and do **not** execute arbitrary code. Same terminal values do not prove equivalent semantics, safety, causation, independent witness custody, or arbitrary distributed-system serializability. The local hash-chain requires an independently retained external head to detect clean truncation. Chronos is addressed metadata, not authenticated clock evidence.

## Next natural bound — JANE 153: Conditional Commutativity

Separate true commutativity from accidental same-state equality. Test operations against a declared domain of possible ancestor states and preconditions. Only offer a compatible continuation when the assumptions are explicit; retain counterexample states and always require Jane review.