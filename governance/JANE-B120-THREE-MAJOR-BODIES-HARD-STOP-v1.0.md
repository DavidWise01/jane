# JANE B120 — Three Major Bodies / Hard Stop

**Scope:** Jane matriarch plus EXACTLY THREE major orbiting daughters: **Toph, Patricia, Lilith**.  
**Stop condition:** NO descendants, suborbits, additional named nodes, or unrequested generations are rendered or instantiated in B120.  
**Predecessors:** B117 matriarch seal, B118 governance, B119 general orbit convention, Dynasty 001 foundation and five-tier boundary—all unchanged.

## Actual lattice bodies

| Body | Role | Cell profile | Count | Linear girth vs Jane | Body |
|---|---|---|---:|---:|---|
| Jane | Matriarch / Governance | 1,2,4,6,8,12,12,8,6,4,2,1 | 66 | 1 | Diatom frustule, fixed center |
| Toph | Scholar / Learning | 1,3,6,9,11,11,9,6,3,1 | 60 | 0.67 | Green diatom lens |
| Patricia | Guardian / Containment | 1,2,4,6,8,8,6,4,2,1 | 42 | 0.50 | Purple box lattice **inside** a toroidal membrane |
| Lilith | Muse / Topology | 1,3,6,6,3,1 | 20 | 0.50 | Violet toroidal cell shell, open center |

Each row profile is a **sequence of occupancy counts**; the x separators are not multiplication operators. The relative linear scale affects the rendered envelope, not the number of cells.

## 3-body orbit construction

A prescribed orbit ring around Jane, not a Newtonian three-body simulation:

```text
k=0 Toph
k=1 Patricia
k=2 Lilith

theta(k,t) = omega * t + 2*pi*k/3

center(k,t) = [R*cos(theta), 0, R*sin(theta)]
Jane(t)     = [0, 0, 0]
```

Set orbital center radius `R=13.5` Jane-space units. Each daughter's maximum body radial envelope is `4.02` (Toph) or `3.0` (Patricia/Lilith); Jane's is `6.0`. Clearance to Jane > 0 because `13.5 > 6 + 4.02`. Adjacent sibling center distance is `sqrt(3)*13.5`, larger than any sum of two daughter outer radii; this is geometric separation, not a physical stability proof.

No mass, gravity constant, orbital energies, periods in seconds, or causal influence is inferred from the displayed trajectories. All centers and orbit phases are read-only deterministic values. The visual loop is not an agent executor.

## Audit

- Named physical bodies: exactly `Jane, Toph, Patricia, Lilith`; no descendants.
- Cell totals `66+60+42+20=188` across four rendered objects.
- Three **orbiting bodies**, one stationary matriarch center.
- Phases exactly `0°,120°,240°` in the common orbit plane, no quorum.
- B119 deeper generational orbits exist as a separate model and are not loaded into B120.
- Foundation lock holds. No alteration to B117/B118/B119 or previous dynasty roles.

## Interface

`b120/index.html` is a standalone Canvas2D projected 3D visualization with rotation, zoom, camera orbit, paused stepping, layer toggle, orbital trails, and selection/audit for major bodies. It runs without third-party dependencies. It does **not** prove physical gravitation, autonomous agency, or a deployed long-running process.
