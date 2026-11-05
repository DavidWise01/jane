# B158 — Source ownership, crossing and witness preservation (pre-ISA)

Preserve the user's `[a:122,b:122,c:122:d:a+b+c::isa]` notation, with `:: isa` **unassigned**. No ISA has been created. No opcodes or dispatcher are authorized.

## The containment invariant

```text
   D  { observe-only derived 366-address view }
    |
    +-- { a / H / a1 } 001 .. 122  [Box62](Toroid60)
    +-- { b / O / b1 } 123 .. 244  [Box62](Toroid60)
    +-- { c / N / c1 } 245 .. 366  [Box62](Toroid60)

   d = a + b + c;  d adds ZERO new cells
```

**An address has one source owner.** D may describe / inspect the union but cannot reassign, duplicate or overwrite source cells, and cannot grant cross-source mutation authority. Each source has an independent witness ledger. Three reports about the same boundary are three observations, not a quorum.

## Seam rules

Local positions 62↔63 mark Box/Toroid seams within each source. Global positions 122↔123 and 244↔245 move into a **different owner**. Since D is the derived view, global 366↔001 also crosses an owner boundary when treating the complete address space as cyclic. A syntactically adjacent cross-source path is labelled **HOLD_SOURCE_WITNESS_REQUIRED**; it does not itself supply authorization, evidence or a source witness. Indexing in reverse uses the same ownership constraints. Ordinary intra-source signed address steps are symbolic, not empirical transitions.

Preserve observations append-only and separately under a1, b1, c1; reject foreign owner claims, duplicate observation identifiers and altered historical records. The Node reference uses SHA-256 chains; the browser local interaction is demonstration-only, and its export is not cryptographically attested.

No measured H/O/N atomic shell structures, force fields or time dilation is inferred. The sole root shadow `{-1,+1}>1` remains unchanged and the five signed spheres are not shadows.

Next boundary: a **read-only cross-source observer** with explicitly separated ingress and egress witnesses, and a failure-preserving hold on unmatched boundary observations, without naming any ISA.
