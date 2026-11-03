# JANE B127 — Reaction-Verified Grandma-to-New-Grandma Handoff

**Additive refinement of B126.** No original dynasty registry, stored isotopes, or earlier source file is rewritten.

## Rule

```text
GRANDMA ELEMENT (Z)
    |
    +-- ENUMERATE ISOTOPES (A,N=A-Z)                  [CATALOGUE]
    |
    +-- OBSERVED REACTION WITH EVIDENCE?             [REACTION]
           |
           +-- conserve baryon number A
           +-- conserve electric charge Q
           +-- conserve electron-family lepton number L
           +-- identify process and conditions
           +-- observe products
           |
           +-- stable product at new Z?
                  YES: NEW GRANDMA [PROMOTE]
                  NO : INTERMEDIATE [PRESERVE, DON'T PROMOTE]
```

The mere presence of a stable element with Z+1 in the chart is a **catalogue traversal**, not evidence that the preceding isotope decays or fuses directly into it.

## Four grounded reactions

1. `H-3 → He-3 + electron + electron antineutrino` — beta-minus, tritium half-life about 12.32 years; **PROMOTE He**. Source: US DOE `https://www.energy.gov/documents/doe-hdbk-1129-2008pdf`.
2. `H-2 + H-3 → He-4 + neutron` — D–T fusion, energy output 17.6 MeV; **PROMOTE He**. Source: `https://www.fusionenergynews.com/kb/deuterium-tritium.html`.
3. `He-3 + He-4 → Be-7 + gamma` — stellar proton-proton chain pathway; **DO NOT PROMOTE Be**, because Be-7 is radioactive, although the element has a stable isotope Be-9. Source: `https://marvin.byu.edu/beryllium7/references/Solar/RepProgPhys-71-106201.pdf`.
4. `Be-7 + electron → Li-7 + electron neutrino` — electron capture; **PROMOTE Li** because Li-7 is stable. Source: same stellar-nuclear review.

## Conservation checker

Every recorded reaction has explicit individual particles `(A,Q,L)`:
- `A`: nucleon number (conserved in these examples).
- `Q`: electric charge (includes electron charge; nuclear proton count Z alone need not be conserved in weak decay).
- `L`: electron-flavor lepton number (+1 electron and electron neutrino; −1 electron antineutrino).
- Gamma rays and neutrinos carry zero baryon number.

The demonstrator is an **accounting and evidence registry**, not a physically complete reaction simulator. Conservation is necessary but **not sufficient** to prove a process occurs; conditions and evidence are required. No energy, momentum, spin, or reaction probability validation is claimed.

## Nonlinear ancestry

A real reaction is often **many-to-many** rather than one Grandma yielding one child. D–T fusion needs *two input nuclei* and has *two nuclear products*. The intermediate Be-7 captures an electron and turns into lithium-7, which shows why the physical reaction graph can move among elements in a different order from atomic-number catalogue traversal.

## Continuity invariant

```text
catalogue_edge != reaction_edge
reaction_edge != guaranteed occurrence
unstable intermediate != stable Grandma
source attribution required
no quorum; no inferred agency
```
