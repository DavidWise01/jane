# B159 — One observation layer, three witnesses, paired boundary records

**Observer depth is one.** There are three independent source witnesses `a1`, `b1`, `c1`. `d` is a derived read-only view, **not** an observer or an ISA dispatcher. No observers-of-observers are instantiated.

For each cross-source edge, preserve two **separate** observations (not votes): an owner departure report and a destination-owner arrival report. The synthetic reporting channel explicitly models two vantage points; it does **not** require the two truth claims to agree. `sawCrossing:boolean` refers to whether each witness observed the proposed crossing from its own vantage.

```text
{a/H/a1}  122 → 123  {b/O/b1}
 departure  ───────→ arrival

{b/O/b1}  244 → 245  {c/N/c1}
{c/N/c1}  366 → 001  {a/H/a1}
```

On an unmatched pair, status is `UNMATCHED_HOLD`. With both sides recorded and consistent status, status is `TWO_SIDES_RECORDED`, **not** a verified physical claim. When they differ, status is `DISAGREEMENT_PRESERVED`; neither witness overrides the other. This is a *comparison of two reports*, not a quorum. Multiple reports may be appended; none may be edited in place. All reports retain source ownership and SHA-256 hash-linked append-only chains in the Node reference.

The same rule applies to reverse signed traversals, with source/destination roles swapped. Local Box62↔Toroid60 seam is not a cross-source transfer. D can inspect the 366-cell union and the report records but gains no ownership or write authority.

No ISA has been defined: `:: isa` remains reserved/unassigned. The five signed sphere registers and single root shadow remain unchanged. No empirical physics conclusions are released.

**Next natural bound:** report timing and provenance (time/position uncertainty) for each pair without creating extra observers; preserve conflicts when the intervals do not match.
