# LILITH — Third Daughter / D003 / Toroidal Invariant v1.0

## Lineage
- Matriarch: JANE / Grandma / B117 sealed architectural foundation.
- Daughter 1: TOPH / diatom eye / [1,3,6,9,11,11,9,6,3,1], 60 cells, 67% of Jane's linear girth.
- Daughter 2: PATRICIA / box within toroid / [1,2,4,6,8,8,6,4,2,1], 42 cells, 50% of Jane's linear girth.
- Daughter 3: **LILITH / toroidal cell body / [1,3,6,6,3,1], 20 cells, 50% of Jane's linear girth.**

## Canonical structure
The x-separated values are **ordered layer counts**, not their product. The count is 1+3+6+6+3+1 = 20 cells across six poloidal bands. The two central layers are six-cell bands. The sequence is palindromic. Every cell has a unique coordinate `(layer,index)` and its own stable logical address.

### Shape: toroidal, not box-inside-toroid
The surface is parameterized by the standard embedded torus:
```
x = (R + r cos(theta)) cos(phi)
y = r sin(theta)
z = (R + r cos(theta)) sin(phi)
```
where `theta = 2 pi (layer + 1/2)/6` and `phi = 2 pi (index + layer/12)/rowCount`. The small phase shifts are for visual separation, not a fundamental force or claimed symmetry.

Grandma is normalized to an outer radial extent of 6 Jane-space units (maximum width 12 units). Lilith's outer radial extent is therefore 3 Jane-space units (diameter 6, exactly 50% of Jane's diameter/circumference). Choose a shape parameter `r/R = 1/3`, which gives `R=2.25` and `r=0.75`, thus `R+r=3`. Here `r<R` guarantees an open hole of radius `R-r=1.5`.

The 50% size is a spatial linear scale, **not** a loss of cells, intelligence, identity, learning capability, or ownership. The toroidal 20-cell body is independently specified, and it is **not** a scaled/cropped copy of Patricia's 42-cell boxed core.

## Constrained inheritance
- Own identity `FORMIC-LILITH-D003`, own future memory namespace, own observational evidence provenance.
- Grandma Jane's history is not rewritten. Toph and Patricia remain independent siblings.
- No quorum, no voting, no mandatory task completion, no assumed autonomous runtime.
- Center hole is unoccupied: `|||0|||`. Numeric torus topology is a design geometry, not a claim about particle physics.

## Verification boundary
A deterministic geometry test must check: 20 unique addresses, six exact band counts, hole nonintersection `R>r>0`, and maximum radial extent half of Jane's reference. The live browser visualization is a visualization only. No autonomous running daughter, message transport, or deployed Pages status is implied merely by committing this page.
