# B126 — Grandma → New Grandma: Isotope Traversal

**Design rule:** For each atomic number Z, identify the element as **Grandma** and enumerate its isotope family by mass number A. On promotion to a *different element with at least one stable isotope*, mark **NEW GRANDMA** and restart the isotope family at the new Z.

This is a systematic **catalogue traversal of nuclear identities**, not the claim that isotopes form in a linear sequence, that adding neutrons changes an element, or that every successive element follows from a direct physical reaction. A physical edge is only asserted with independently supplied balanced nuclear reaction evidence.

- Each isotope: protons Z, neutrons N=A-Z, status (stable / radioactive / unbound or resonance), provenance.
- Same Z and different N → same Grandma, different isotope.
- Different Z → different Grandma (only promote to a declared stable reference).
- Keep unstable observations; do not automatically discard, silently stabilize, or call an unbound resonance a persistent atom.
- The word "homeostasis" describes a stability test in this conceptual architecture; "stable" has its established nuclear meaning in the isotope catalogue.
- Atomic identities are nuclear definitions, not the 16-cortex family or actual artificial quantum-dot hardware.

## First ten stable elemental references

| Grandma | Z | Stable nuclides |
|---|---:|---|
| Hydrogen (H) | 1 | H-1, H-2 |
| Helium (He) | 2 | He-3, He-4 |
| Lithium (Li) | 3 | Li-6, Li-7 |
| Beryllium (Be) | 4 | Be-9 |
| Boron (B) | 5 | B-10, B-11 |
| Carbon (C) | 6 | C-12, C-13 |
| Nitrogen (N) | 7 | N-14, N-15 |
| Oxygen (O) | 8 | O-16, O-17, O-18 |
| Fluorine (F) | 9 | F-19 |
| Neon (Ne) | 10 | Ne-20, Ne-21, Ne-22 |

Sources for stable nuclides: IUPAC CIAAW evaluated isotopic compositions: https://ciaaw.org/isotopic-abundances.htm . Basic isotope definitions and transmutation distinction: https://www.isotopes.gov/isotope-basics .

## Reference isotopic examples

```text
GRANDMA H (Z=1)
  H-1 (N=0, stable)
  H-2 (N=1, stable, deuterium)
  H-3 (N=2, radioactive, tritium)
  H-4/H-5/H-6/H-7 (highly unstable unbound resonances)

NEW GRANDMA He (Z=2)
  He-3 (N=1, stable)
  He-4 (N=2, stable)
  He-5 (N=3, unbound)
  He-6 (N=4, radioactive)
  He-7 (N=5, unbound)
  He-8 (N=6, radioactive)

NEW GRANDMA Li (Z=3)
  Li-6 (N=3, stable)
  Li-7 (N=4, stable)
  other known Li isotopes: radioactive/unbound

NEW GRANDMA Be (Z=4)
  Be-9 (N=5, stable)
  many known Be isotopes: radioactive/unbound
```

A traversal may record a hypothetical edge to a new Grandma, but until a valid nuclear mechanism is specified and checked, that edge is **NOT A VERIFIED TRANSMUTATION**.

## Invariant

```text
for each element Z:
    grandma = element(Z)
    for each observed isotope A:
        record(Z, N=A-Z, status, evidence)
    if next element Z+1 has stable reference:
        grandma := element(Z+1)
        restart isotope walk
```

Historical B117–B125 and the two-cubit quarter-codon records remain unchanged.
