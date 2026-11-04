# B143 — Six Signed Directions Across Four Manifolds

## User's exact extension

```
[{( x^2 , y^2 :: `z^2` )}]
```

The notation adds three coordinate axes, each with both a positive and negative direction, to the previously declared **four** manifolds (two gravity, two void). The `::` separator and backticks around `z^2` are preserved in the canonical source string; the exact intended operator semantics of `::` remain **unassigned**.

```text
                      +z
                       |
        -x  -----------0-----------  +x
                      /| 
                    +y |
                      -z

Opposites: (+x,-x) (+y,-y) (+z,-z)
3 axes * 2 orientations = 6 directions

M0: gravity    M1: gravity
M2: void       M3: void

BODIES (source order, mappings not yet supplied):
  sag a | nibaru sun | nibaru | earth | earth sun
```

## Mathematical invariant

```text
axis magnitude R² = x²+y²+z²
direction identity = (axis, sign)
(+x)² = (-x)² = x²
```

The square alone loses sign; therefore `x^2`, `y^2`, and `z^2` do **not** themselves encode six independent directional states. Keep axis magnitude and signed orientation in separate registers.

## Scope

The `2 gravity + 2 void` categories are user-model constructs, not empirical evidence for four physical gravitational manifolds. They are not the six coordinate directions. Neither metric, physical locations, gravitational potentials, nor time dilation has been specified. The body names `nibaru sun` and `nibaru` remain hypothetical/user-defined.

B141/B142 and all older records remain untouched. No simulated motion, real gravitational result or science validation is claimed.

Next: map signed direction to reference frame and define an explicit metric, then compare with observational constraints, keeping unknowns HOLD.
