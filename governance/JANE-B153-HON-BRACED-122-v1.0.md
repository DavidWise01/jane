# B153 — Three Braced Scouts: H / O / N, Box62 + Toroid60

User-defined structural bound:

```text
{ H / a1 }     001 ... 122
{ O / b1 }     123 ... 244
{ N / c1 }     245 ... 366

BOX62  [1×2×4×6×8×12×12×8×6×2×1]    62 cells
TOR60  (1×3×6×9×11×11×9×6×3×1)        60 cells
       62 + 60                         122 per brace
       H + O + N                       366 total
```

**Important syntax:** The user's ×-delimited lists are treated as a *sequence of layer populations*, not mathematical multiplication of those integers. They sum to 62 and 60 respectively. These are numbered logical registers, not experimental electron occupancy shells.

## Canonical mapping
Within each brace, local positions **001–062** belong to Box62 and **063–122** to Toroid60. The three braces have disjoint global ranges H=001–122, O=123–244, N=245–366, with the witness routing `a1→H`, `b1→O`, `c1→N`. No quorum or shared witness vote.

The two signs `-` (reverse / inward) and `+` (forward / outward) are **direction labels on the same cells**, not extra positions, duplicate shadow copies, or evidence of physical charge. A reversible traversal wraps around local 122→001 and 001→122; the Box/Toroid seam is 062↔063. This is a computational visualization convention, not an assertion of atomic wave functions.

The first shadow operation `{-1,+1}>1` applies **only once at the root**. The remaining five S1–S5 sphere registers do not acquire shadows.

## Animation
The Git Pages `b153/index.html` extends the B152 pixel-art arcade with three individual animated 3D-perspective projected point clouds. The 11 box layer populations and 10 toroid layer populations form 122 colored pixels per brace; each code monkey moves through its own cells, leaving a signed traversal trail and independent observations. Focus and manual polarity controls can be used to inspect the current local/global address and layer index.

## Physical gate
H, O, N are user-defined computational brace names here; the 62/60 cells are not literal hydrogen, oxygen or nitrogen electron shell counts. The perspective scene and -/+ traversals are a hypothetical logical model. No physical gravity, distance or time-dilation claim is promoted; no empirically verified charge assignment follows from the signs.

Next natural bound: instrument a local 122-slot loop for each scout; compare reverse and forward walks over Box/Toroid seams with per-scout immutable checkpoint logs, preserving failures independently.
