# B157 — Pre-ISA boundary: no instruction set exists yet

The corrected canonical structure is **`[a:122 , b:122 , c:122 : d: a+b+c :: isa]`**.

The `:: isa` token is a **reserved, undefined marker**. It is **NOT** a defined instruction set, processor, or dispatcher. Earlier B155 and B156 files mistakenly treated it as an implemented ISA. Keep those files as historical experiments, but do not promote their opcodes or instruction interpretations as user-authorized architecture.

```text
[a:122 , b:122 , c:122 : d: a+b+c :: isa]
   |       |       |      |            |
 {H/a1}  {O/b1}  {N/c1}  366         UNASSIGNED
  1–122  123–244 245–366 derived
  Box62  Box62   Box62
  Tor60  Tor60   Tor60

 ISA INSTRUCTIONS DEFINED: 0
```

Exactly three braced source registers, each 62 Box cells plus 60 Toroid cells. Their global cell ranges are disjoint and fixed. `d` is the derived, read-only concatenation of the three 122-cell sources; it allocates no fourth register. The only observed behavior specified is **addressing, observing and signed index transitions** through the three cages. These are geometry operations, NOT an ISA or opcodes.

A human can explore this structure in the original retro pixel-art atom laboratory via three H/O/N scout selectors. A visual signed `+` or `−` index walk is a conceptual animation, not physical charge, nor verified electron-shell occupancy. Root shadow applies only to `{-1,+1}>1`; the five signed spheres are not shadows. No quorum, no votes, no empirical physics promotion.

**Next natural bound:** derive formal `d` containment and routing topology from the three preserved source registers, explicitly leaving every undefined operation HOLD. Only name or specify an instruction language when its syntax, authority, and semantics have actually been supplied.
