# JANE B146.2 — Natural positional remap of corrected five-body gravity frame

## Canonical order
```text
0 sag a
1 nib sun
2 nib
3 earth
4 earth sun
```

## Remap invariant
Remap *indices*, not presumed orbital physics. Preserve the six earlier B146 connection IDs, exact notation, distance bands, force bands, and source order. Apply the index-pair relationships `(0,1),(1,2),(2,3),(3,4),(0,2),(0,3)` to the B146.1 canonical order.

| Source edge | Remapped connection | Original distance |
| --- | --- | --- |
| u1 `x²` | sag a ↔ nib sun | long |
| u2 `y²` | nib sun ↔ nib | medium |
| u3 `z²` | nib ↔ earth | medium |
| u4 `x²::y²` | earth ↔ earth sun | short |
| u5 `y²::z²` | sag a ↔ nib | unquantified |
| u6 `z²::x²` | sag a ↔ earth | unquantified |

This is the minimum change consistent with the corrected list order and preservation of connection slots. It is a *model remap*, not new evidence about astronomical bodies.

The first four bodies are designated the four **logical core vertices**, the fifth is a **terminal referent** for the fourth consecutive connection. This is graph bookkeeping, **not an assertion that Earth Sun is physically nested inside Earth**.

A complete four-vertex tetrahedral graph has six core edges. This preserved source graph has five such edges and one terminal link; it omits `nib sun↔earth`. We do not invent it. The full tetrahedral interpretation remains **HOLD**, despite the valid positional remap.

Both gravity and void fields remain model-specific labels; the six signed spatial directions remain unchanged. Numerical interbody separation, real orbital dynamics, and proper-time prediction remain **HOLD** until measurements/metric are supplied. The B146 and B146.1 records are append-only historical provenance and are not rewritten.

## Test boundary
Node regression confirms six remapped slots, their original notation, the core-vs-terminal distinction, and rejects eight synthetic mutations (including invented distances and improper clock predictions).
