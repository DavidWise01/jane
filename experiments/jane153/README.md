# JANE 153 — Conditional Commutativity

**Invariant:** A(B(s)) = B(A(s)) must be established across a declared domain, considering execution validity and final state. A single compatible ancestor cannot establish universal compatibility.

Canonical FLAY address: `{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ ancestor / child }}`.

## Executed fixture

A is `set(0)`. B is `conditional_add(0)`, whose precondition requires its input to be nonnegative. Over [-3, 3], both execution orders agree at states 0, 1, 2, and 3, but disagree in validity at -3, -2, and -1. The smallest counterexample by absolute value is **-1**. This is conditional compatibility, not universal compatibility. The engine preserves the smallest counterexample and both traces in a hash-linked, append-only event log.

**30/30 Python tests passed locally.** Run `python -m unittest discover -s . -p 'test_*.py' -v` from this directory. Dependencies: Python 3.10+, standard library only.

The parent remains frozen; Jane's learning decision is UNDECIDED. The results are bounded, synthetic computation, not a general theorem for arbitrary programs or independently witnessed evidence. Local hash chaining does not detect valid tail deletion without an externally retained head.

## Next bound — JANE 154: Domain Boundary Search

When two operations appear compatible on an enumerated domain, test adjacent boundary states, preserve witnesses of the domain assumptions, and avoid extrapolation past a verified boundary.