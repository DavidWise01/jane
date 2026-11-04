# JANE B128 — Elemental Grandma Branch Growth

**Continues B127.** The Grandma role transfers only when a documented reaction produces a stable nuclide of a different element. Do not confuse this with the separate catalogue walk through consecutive atomic numbers.

## Branches

1. `Li-7 + He-4 -> B-11 + gamma` : measured 7Li(alpha,gamma)11B reaction. New Grandma **Boron** (B-11). Source: Brookhaven NNDC ENSDF, https://www.nndc.bnl.gov/ensdf/getrefs.jsp?dsid=7LI%28A%2CG%29+RES&recid=11005007
2. `B-11 + H-1 -> C-12 + gamma` : measured 11B(p,gamma)12C channel. New Grandma **Carbon** (C-12). Source: Phys Rev C 109, 014619 (2024), https://doi.org/10.1103/PhysRevC.109.014619
3. `C-12 + He-4 -> O-16 + gamma` : measured radiative alpha capture; important to stellar helium burning. New Grandma **Oxygen** (O-16). Source: Phys Rev Lett 86, 3244 (2001), https://pubmed.ncbi.nlm.nih.gov/11327941/
4. `O-16 + He-4 -> Ne-20 + gamma` : alpha capture in stellar nucleosynthesis. New Grandma **Neon** (Ne-20). Source: nuclear astrophysics overview, https://www.sciencedirect.com/science/article/pii/S0924809906800296
5. `He-4 + He-4 <-> Be-8` : unstable Be-8 intermediate, do NOT promote to Beryllium Grandma. Important in the triple-alpha pathway; the net result with a third alpha particle is C-12. Source: same nuclear astrophysics overview.

## Graph

```text
Grandma Lithium-7 + Helium-4
         |
         v
New Grandma Boron-11 + proton
         |
         v
New Grandma Carbon-12 + alpha
         |
         v
New Grandma Oxygen-16 + alpha
         |
         v
New Grandma Neon-20

Other branch:
He-4 + He-4 -> Be-8 (unstable; not Grandma)
                     + He-4 -> C-12 via triple-alpha
```

## Requirements

- All reaction records maintain nucleus/nucleon balance `A` and total nuclear charge `Z`. Gammas contribute zero A/Z.
- **Conservation is necessary, not sufficient:** these checks do not calculate nuclear mass differences, electromagnetic transitions, cross sections, environment thresholds, reaction rates, momentum, or competing processes.
- All five pathways include external published sources; sources describe measurements or established astrophysical reaction pathways, **not arbitrary reactions at ambient conditions**.
- Existing isotope-family enumerations stay separate. Every promoted elemental Grandma must be expanded into its isotope family in a subsequent dedicated record, rather than presenting the specific product as the entire family.
- Beryllium is NOT globally barred from the Grandma role: stable Be-9 exists, but the documented branch here yields **unbound Be-8**, so no Beryllium-8 promotion.
- Preserve B117–B127, the sixteen-cortex family, role provenance, and quarter-codon logical cubit definitions without modification.
