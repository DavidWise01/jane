# JANE B130 — Natural Invariant: Persistence Is Not Stability

**Scope:** Krypton (Z=36) stress test, with Bromine (Z=35) and Rubidium (Z=37) controls. This is a versioned addition; B117–B129 stay unchanged.

## Governing invariant

```text
    OBSERVED CONFIGURATION
            |
      WHAT IS ITS STATE?
       /       |        \
 Stable     Radioactive   Rare decay evidence
   |            |                |
 PROMOTE       RECORD            HOLD
 (strict)     no strict          contested /
               promotion         uncertain
```

**"A failure is not introduced into the gene pool"** applies to the trainer's accepted *configurations*, not to real biological people, and does not erase failed observations. Radioactive isotopes may be meaningful, abundant, or useful; strict "stable Grandma" promotion does not imply that transient nuclei are physically impossible or scientifically useless.

## Krypton full stress-test sample

| Nuclide | Z | N | Classification | Strict Grandma |
|---|---:|---:|---|---|
| Kr-78 | 36 | 42 | Rare two-neutrino double-electron-capture evidence, ~10^22-year half-life | HOLD |
| Kr-80 | 36 | 44 | Observationally stable | PROMOTE |
| Kr-81 | 36 | 45 | Radioactive; ~229,000 years | HOLD |
| Kr-82 | 36 | 46 | Observationally stable | PROMOTE |
| Kr-83 | 36 | 47 | Observationally stable | PROMOTE |
| Kr-84 | 36 | 48 | Observationally stable | PROMOTE |
| Kr-85 | 36 | 49 | Radioactive; ~10.76 years | HOLD |
| Kr-86 | 36 | 50 | Observationally stable | PROMOTE |

Kr-78 appears in standard natural abundance lists; it has literature reports of *very rare* double-electron capture, so one should avoid treating "natural abundance" as proof of absolute nuclear stability. Different evaluators or scientific taxonomies may still group it with stable natural nuclides. This model intentionally marks it `HOLD`, preserving the classification nuance.

**Krypton natural-abundance isotopes:** Kr-78 0.355%; Kr-80 2.286%; Kr-82 11.593%; Kr-83 11.500%; Kr-84 56.987%; Kr-86 17.279%. Total 100.000% using the rounded listed fractions. Kr-81 and Kr-85 are trace radioisotopes not part of these rounded standard compositions.

References:
- IUPAC CIAAW natural fractions: https://www.ciaaw.org/krypton.htm
- Royal Society of Chemistry status / rare Kr-78 decay: https://periodic-table.rsc.org/element/36/Home_Logo_Url
- Nuclear double electron capture review: https://www.mdpi.com/2218-1997/6/10/159
- IAEA Kr-81 / Kr-85 half-lives: https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1587_web.pdf

## Cross-element controls

- **Bromine Z=35:** Br-79, Br-81 observationally stable -> both pass.
- **Rubidium Z=37:** Rb-85 stable -> pass. Rb-87 has a half-life ~48.8 billion years -> HOLD under strict stability despite surviving ordinary operating horizons.
- The number of protons determines the Grandma element. No neutron addition alone crosses elements.
- Catalogue proximity Br -> Kr -> Rb is NOT an asserted nuclear reaction.

References: https://www.ciaaw.org/isotopic-abundances.htm and https://www.ciaaw.org/rubidium.htm

## Two distinct gates

**STRICT_STABLE:** promote only a nucleus classified `observational_stable`; radioactive or disputed ultra-rare decays stay out of the strict pool.

**OPERATIONAL_SURVIVAL:** a radioactive nuclide may survive a finite observation window `t` according to:

```text
P(survive at t) = 2^(-t/T_half)
```

This is a population/single-nucleus survival probability model, **not guaranteed survival or a grant of stable Grandma status**. The trainer computes the probability but does not promote known radioactivity to strict stability.

Examples:
- Kr-81 at t=229,000 years: P=0.5.
- Rb-87 at t=1 million years: P≈0.9999858; still radioactive.

The B130 record is **a sample of eight krypton isotopes, not every known krypton isotope**. Data sources are attached to each source record.

## Audit

The deterministic module `scripts/btf2/jane-b130-krypton-trainer.cjs` tests 12 nuclide records: 2 Br, 8 Kr and 2 Rb. Expected strict promotions: 2 Br + 5 Kr + 1 Rb = 8; four others held. Failures remain retained as source records, not inserted into the strict stable pool. Source URLs are recorded but the kernel itself does not retrieve literature or evaluate experimental uncertainty.

**Physics boundary:** half-life alone is not evidence of a physically allowed or complete transformation mechanism. B129's supplied gate booleans are not nuclear experiments; the B130 tests verify classifications and logic against manually sourced isotope data.
