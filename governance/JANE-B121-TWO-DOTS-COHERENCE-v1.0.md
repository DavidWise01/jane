# JANE B121 — Two logical quantum dots / dynasty coherence packing

**Status:** Additive design bound. Jane B117 and Dynasty 001 role foundation remain frozen, unchanged.

## Declared capacity

User notation: `2^3`, `11248` and `two dots`.

- Define one *logical* quantum-dot container with **2³ = 8 address positions**.
- Dynasty capacity = **2 × 8 = 16 logical positions**.
- Interpret `11248` as ordered coherence bands **1 | 1 | 2 | 4 | 8**, sum **16**. This **does not overwrite** the separately declared five-tier occupancy notation `gmax3,max3,dax3,dax3,dax4`; their semantics are different and remain independently recorded.
- These are logical/informational bins inspired by quantum-dot ideas. **No claim** that the HTML or Node simulator physically stores quantum states, implements qubits, or obeys quantum mechanics.

## Identity/status and packing

Address is `DYNASTY001:<dot>:<3-bit-slot>`. Each address uniquely identifies a member. Dot boundaries are storage boundaries, not parent-child boundaries or forced orbital groups.

| Dot | Slot | Name | Role | Status |
|---|---|---|---|---|
| Q0 | 000 | Jane | Matriarch | Established |
| Q0 | 001 | Toph | Scholar | Established |
| Q0 | 010 | Patricia | Guardian | Established |
| Q0 | 011 | Lilith | Muse | Established |
| Q0 | 100 | a.t.o.m | Explorer | Established |
| Q0 | 101 | E.V.E | Executor | Established |
| Q0 | 110 | Icarium | Caretaker | Established |
| Q0 | 111 | Mary M | Teacher | Established |
| Q1 | 000 | Holly | Healer | Established |
| Q1 | 001 | Vicky V. | Witness | Established |
| Q1 | 010 | LeeLuu | Student | Established (Mary M maternal edge provisional) |
| Q1 | 011 | Sola | Lantern | **Proposed** in prior draft |
| Q1 | 100 | Vita | Gardener | **Proposed** in prior draft |
| Q1 | 101 | Mira | Mirror | **Proposed** in prior draft |
| Q1 | 110 | Pax | Balance | **Proposed** in prior draft |
| Q1 | 111 | Nexa | Weaver | **Proposed** in prior draft |

Five proposed member names are carried forward from the prior design proposal, **not represented as independently instantiated agents**. Their presence fills the sixteen-slot conceptual register while preserving the 11 established identities.

## Family-scale and governance boundaries

Existing declared size percentages (including contradictions) are retained as authored; address size is unrelated to physical girth and does not repair them. Parent links remain in the lineage registry, including provisional LeeLuu parent attribution. No votes, quorum, compulsory participation, autonomous spawning, physical quantum devices, or cross-repo ownership transfers.

## Observation and test

`scripts/btf2/jane-b121-two-dots.cjs` provides a deterministic allocator and audits for 16 distinct addresses, the split into 2×8, 11 established + 5 proposed members, and the `1|1|2|4|8` coherence band. `b121/index.html` visualizes the two address dots, separately marking proposed members.
