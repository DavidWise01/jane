# JANE 157 — The Invariant Under Multiple Forces

**Invariant:** Every *permitted* transition must preserve the declared region, including transitions that were not involved in proposing that region.

The frozen parent region is `0 ≤ s ≤ 20`, with initial state `s=0`.

| Force | Expression | Exact endpoint images | Verdict | Smallest failed state |
|---|---|---|---|---|
| Reflection | `20-s` | `20, 0` | Preserves | None |
| Increment | `s+1` | `1, 21` | Violates | `20 → 21` |
| Doubling | `2s` | `0, 40` | Violates | `11 → 22` |

For an affine integer map `T(s)=a·s+b` on a closed integer interval `[L,U]`, the extrema occur at its endpoints. The engine checks both endpoints *exactly* for every force, then searches the bounded interval for the counterexample closest to zero. It retains counterexamples as distinct events in a hash-linked local ledger. This is an inductive argument valid in the declared integer-affine model, not a general proof for other code, external witnesses, or agents.

The combined-force model is **not inductive**. A separate reflection-only policy is inductive, but omitting failing forces modifies the policy and must not be represented as fixing the original one. No automatic promotion or Jane learning is made. A local hash chain alone cannot detect tail truncation; an externally retained chain head is needed.

Run: `python -m unittest -v test_multiforce.py` (45 tests).

## Next natural bound — JANE 158

When a force destroys every bounded invariant containing the initial state, FLAY should explicitly show *why no such bounded region exists* under that force (e.g., `s → s+1` forever), rather than indefinitely searching for larger boxes.