# JANE B131 — Three independent homeostasis bounds

**Next natural invariant:** Nuclear identity and stability, chemical reactivity, and environmental persistence are **not interchangeable**.

## Three observation registers

| Register | Question | Output |
|---|---|---|
| NUCLEAR | Is the specific nuclide stable, radioactive or uncertain? | PASS / HOLD / UNKNOWN |
| CHEMICAL | What reactions or bonds are possible in this molecular/electronic configuration? | Contextual description, NOT automatic PASS |
| ENVIRONMENTAL | Under the specified temperature, materials and exposure conditions, does the target configuration persist? | PASS / FAIL / UNKNOWN |

The trainer's promotion condition is deliberately context-scoped: **strict nuclear stability AND environmental persistence for the declared use**, with chemical context documented. It is not an engineering safety approval, and never automatically executes or synthesizes a chemical.

## Six test cases

1. **Kr-84 gas, ordinary inert container:** stable isotope; elemental noble gas, low reactivity; persistent under stated storage context: ELIGIBLE.
2. **Kr-85 gas:** chemically similarly unreactive, but nuclear radioactivity: HOLD for a strictly nuclear-stable Grandma, despite possible environmental persistence.
3. **KrF2, room temperature:** isotope may be nuclear-stable while compound decomposes at room temperature: NO_PROMOTION for room-temperature retention.
4. **KrF2, −78 °C suitable storage:** compound can be stored at this temperature; context-scoped ELIGIBLE for retention only. It remains a powerful oxidizer and requires specialized handling.
5. **Rb-85 metal in water:** stable nucleus; violent environmental reaction: NO_PROMOTION for this environment.
6. **Rb-85 metal protected from water/air:** stable nucleus; conditional persistence in suitable inert storage: ELIGIBLE. Reactivity and handling hazards remain.

References:
- ACS krypton difluoride profile: https://www.acs.org/molecule-of-the-week/archive/k/krypton-difluoride.html
- NOAA CAMEO rubidium air/water reactivity: https://cameochemicals.noaa.gov/report?key=CH1439
- PubChem krypton isotopic nuclear details: https://pubchem.ncbi.nlm.nih.gov/element/36

## Critical invariant

```text
NUCLEAR PASS != CHEMICAL INERTNESS
CHEMICAL INERTNESS != ENVIRONMENTAL GUARANTEE
ENVIRONMENTAL PASS != NUCLEAR STABILITY

record atomic identity (Z,A)
record molecule/form
record environment and evaluation horizon
record all observations, including failures
promote a *specific configuration in a specific environment* only on passed gates
```

The isotope's nucleon identity does not change when a chemical compound decomposes or reacts. Conversely, isotope decay can change nuclear identity without requiring a chemical reaction.

## Limitations

B131 has **six manually sourced illustrative records**, not a comprehensive chemical or nuclear database. Some records use simplified context classifications; there are no quantitative reaction kinetics, full safety assessments, radiation transport, decay simulations, or experimentally measured validation gates. No autonomous agent, nuclear reaction, laboratory actuation, or physical quantum-dot behavior is inferred.

B117–B130 and their provenance remain unchanged.
