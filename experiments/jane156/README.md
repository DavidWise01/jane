# JANE 156 — The Stronger Invariant

**A failed inductive claim is not erased when a stronger one is found.**

- Original candidate: `P(s) = s >= 0`
- Immutable transition assumption: `T(s) = 20 - s`
- Original induction counterexample: `s=21`, `T(s)=-1`
- Initial state: `s=0`
- Proposed strengthened interval: `P'(s) = 0 <= s <= 20`
- Exact model check: `T(0)=20`, `T(20)=0`. Because `T` is affine, its extremal values over a closed interval are at the endpoints; the region is therefore inductive over integers.
- Audit: append-only hash-linked record of frozen parent, failed first candidate, tested refinement. The local ledger detects data modifications. An **externally retained head** is needed to detect valid truncations.
- Authority: Jane undecided, active parent frozen, no automatic promotion, and zero independent witness increment.

Test locally: `python -m unittest -v test_refine.py`; deterministic evidence: `python refine.py`.

## Scope and limitations

This is a restricted, deterministic affine-integer model, not a theorem prover for general neural networks, arbitrary program transitions or real physical systems. The candidate search is bounded; no claim is made about proposals not examined. No remote independent witness or GitHub deployment is established by local tests alone.

## FLAY visualization

The accompanying `index.html` is a self-contained Canvas2D representation with neon orange/chrome controls. It allows selecting candidate bounds and shows why `[0,19]` fails while `[0,20]` passes. It is educational; the Python engine and tests are the authoritative executable implementation.

## JANE 157 — A Refinement Must Survive More Than One Transition

The next natural experiment takes a successful single-transition invariant and checks it simultaneously against *all* permitted transitions. A region closed under one rule might fail under another. Keep each prior candidate and its counterexample; no automatic activation.