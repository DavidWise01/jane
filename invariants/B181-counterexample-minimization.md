# B181 — Counterexample Minimization

Status: **locally tested (7/7)**. Integration with B180 parsers is pending; no live B180 disagreement has been claimed.

## Invariant

For a B180 disagreement x0, preserve x0 unchanged and find a bounded smaller witness xm such that

- bytes(xm) <= bytes(x0);
- left.accepted(xm) = left.accepted(x0);
- right.accepted(xm) = right.accepted(x0);
- left.category(xm) = left.category(x0);
- right.category(xm) = right.category(x0).

The minimizing algorithm is deterministic chunk deletion over Unicode code points. A candidate is accepted only when all four components match; evaluation exceptions reject the candidate.

## Bounds

- Maximum original input: 16384 UTF-8 bytes. Oversized inputs receive INPUT_LIMIT without evaluation.
- Maximum candidate evaluations: 256 per counterexample.
- Maximum passes: 32 per counterexample.
- Maximum B180 cases: 12; extras are rejected rather than silently omitted.
- No counterexamples: NO_COUNTEREXAMPLES.
- Original input and minimized witness both carry SHA-256 and byte lengths.
- Termination is bounded; global minimality is **not** asserted.

## Interface

`minimizeCounterexample(original, evaluate, limits)` expects an evaluator that returns:

```js
{
  left: { accepted: false, category: 'E_LEFT' },
  right: { accepted: true, category: 'OK' }
}
```

`minimizeB180Cases(cases, evaluate, limits)` processes up to twelve stored B180 inputs.

## Witness policy

NO DISAGREEMENT -> NO_DISAGREEMENT, original unchanged.
DISAGREEMENT -> MINIMIZED or UNCHANGED, with exact signature and original.
LIMIT HIT -> INPUT_LIMIT or exhausted true; no invented proof of minimum.
PARSER THROW DURING REDUCTION -> candidate rejected, last verified witness retained.

This document specifies B181 without modifying the frozen B180/B179 logic.
