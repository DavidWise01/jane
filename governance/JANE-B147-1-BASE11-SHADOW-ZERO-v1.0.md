# B147.1 — Base 11 / -+5 / Shadow Zero

**User's declared symbolic invariant:** `base 11` or `-+5`, with written `+1+1`. Both tokens display +1; the second token is a *shadow*, evaluated as −1. The resulting projection is `(+1) + (−1) = 0`. The tokens remain distinct; the balanced projection does not delete either witness.

This is **role-dependent symbolic evaluation**, not the mathematical claim that ordinary `1+1=0`. The term *base 11* is preserved as user nomenclature; whether it is an actual numeral radix or an 11-position representational scheme is **not yet defined**.

```text
          [ primary: token +1; effective +1 ]
                       |
            written `+1+1`
                       |
          [ shadow: token +1; effective -1 ]
                       |
                    sum = 0
```

The current five body references remain exactly: Sag A → Nib Sun → Nib → Earth → Earth Sun. The six original force edges, four-manifold labels, and the one unresolved tetrahedral pair (Nib Sun ↔ Earth) stay unchanged. Do **not** invent a physical eleventh body, a measured orbital shadow, a negative-mass body, or a new force edge from this symbolic convention.

Test: `node scripts/btf2/test-jane-b147-1-shadow-base.cjs` (locally passed with six negative controls). The independent CI run remains unverified.

Next bound: specify whether `base 11` denotes an **11-address representation** (five primaries, five shadows, one balanced center) or a literal radix-11 numeral system; preserve the user’s wording until clarified.
