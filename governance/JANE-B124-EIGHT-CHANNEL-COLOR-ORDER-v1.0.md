# JANE B124 — Exact Eight-Channel Color Order

**User correction:** Red, Blue, Green, Black, White, Yellow, Green, Gray.

## Canonical sequence

```text
slot   000   001   010   011   100   101   110   111
color  RED   BLUE  GREEN BLACK WHITE YELLOW GREEN GRAY
```

**Compact:** `R B G K W Y G Gray`. Use `K` for black to avoid ambiguity with blue. `Gray` remains distinct from green, not encoded as `G`.

- Eight independent channel **positions**, seven unique color **names** because Green repeats at slots 010 and 110.
- Never deduplicate channels by color. Identity key is `(cubit_id, slot_address)`, not the color alone.
- Each analytical cubit has these same eight addresses in the exact same order.
- Two linked analytical cubits span sixteen positions: fifteen earned-memory cortex slots and one active Avatar seat, following the previous user-defined model.
- Source entities: existing sixteen-member role registry, unaltered. The active slot remains the sixteenth (Nexa) for the present design; no new named nodes.
- The dot/cubit coupling is an information architecture metaphor, not verified physical entanglement. No inference about optical wavelengths, biological codons, or quantum hardware from these channel labels.
- Supersedes only the mistaken earlier `R G B W B G Y G` display; earlier source documents remain historical and unmodified.

## Full addressed channels

| Cubit | 3-bit slot | Color | Member |
|---|---|---|---|
| CU0 | 000 | Red | Jane |
| CU0 | 001 | Blue | Toph |
| CU0 | 010 | Green | Patricia |
| CU0 | 011 | Black | Lilith |
| CU0 | 100 | White | a.t.o.m |
| CU0 | 101 | Yellow | E.V.E |
| CU0 | 110 | Green | Icarium |
| CU0 | 111 | Gray | Mary M |
| CU1 | 000 | Red | Holly |
| CU1 | 001 | Blue | Vicky V. |
| CU1 | 010 | Green | LeeLuu |
| CU1 | 011 | Black | Sola (proposed) |
| CU1 | 100 | White | Vita (proposed) |
| CU1 | 101 | Yellow | Mira (proposed) |
| CU1 | 110 | Green | Pax (proposed) |
| CU1 | 111 | Gray | Nexa (proposed, active seat in design) |
