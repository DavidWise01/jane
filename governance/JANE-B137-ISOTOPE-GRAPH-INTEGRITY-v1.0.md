# JANE B137 — Bounded Isotope Completeness / Reaction-Graph Integrity

## The natural invariant

**A complete declared dataset is NOT a complete census of nature.**

1. CIAAW reports representative natural isotopic compositions, and can include radioactive but very long-lived members. Its rows are **not** a list of all nuclides or definitive proof of nuclear stability.
2. IAEA LiveChart / ENSDF provides nuclear structure and decay-property information. A genuine all-known-nuclides census must ingest and version that evaluated dataset; **B137 does not yet do so**.
3. A documented, arithmetically balanced reaction edge is not proof that the process takes place under arbitrary conditions. Unsupported or unresolved edges remain UNKNOWN/HOLD.

Sources:
- CIAAW 2024 isotopic compositions: https://ciaaw.org/isotopic-abundances.htm
- CIAAW krypton: https://www.ciaaw.org/krypton.htm
- IAEA LiveChart/ENSDF: https://nucleus.iaea.org/Pages/livechart-of-nuclides-av.aspx

## Declared finite abundance scope

The 11 selected elements are H, He, Li, Be, B, C, N, O, F, Ne, Kr. The natural isotope-mass entries listed in CIAAW for these elements are:

```
H  : 1,2          He : 3,4         Li : 6,7
Be : 9            B  : 10,11       C  : 12,13
N  : 14,15        O  : 16,17,18    F  : 19
Ne : 20,21,22     Kr : 78,80,82,83,84,86
```

Total 26 *composition entries*, plus two supplementary trace krypton radionuclides Kr-81, Kr-85 (28 records overall). The CIAAW abundance entries are 100% accounted for **within this declared subset**, but no percentage of *all known nuclear isotopes* is claimed.

**Kr-78 warning:** CIAAW lists Kr-78 among naturally occurring krypton isotopes. The prior B130 strict promotion policy holds it as rare-decay evidence. These two claims are logically compatible: naturally occurring does not imply strictly nonradioactive. B137 does not rewrite B130.

## Reaction edge checks

B137 imports the five previously recorded B128 edges as read-only input (Li-7(alpha,gamma)B-11; B-11(p,gamma)C-12; C-12(alpha,gamma)O-16; O-16(alpha,gamma)Ne-20; He-4 + He-4 -> Be-8). It checks **A and Z conservation** and whether a source link is recorded; it does not independently read the cited papers or calculate cross-sections. Missing participants → HOLD; wrong conservation → REJECT; missing source → HOLD.

These five paths are **already-existing sample edges**, not a comprehensive reaction database, and B137 introduces zero new physical reaction hypotheses.

## What's still missing

- Fetch, snapshot/version and parse an evaluated ENSDF/LiveChart nuclide dataset.
- Compare completeness against an explicit total set of known nuclides at an identified evaluation date.
- Reconcile status of rare decays and limits with evaluation uncertainty and dated references.
- Verify each reaction primary literature and measured domain of validity.
- Add energy, momentum, branch probability / cross-section gates.
- No false 'known all isotopes' percentages. Missing census = UNKNOWN.

## Test

The B137 Node test validates 26 natural records, two supplemental Kr isotopes, eleven exact declared scope checks, five inherited reaction accounting checks, unknown nuclei, gap reporting, unsourced paths, and unbalanced paths. This is an **accounting test** not an empirical validation.

This is append-only relative to B117–B136. The sixteen-cortex two-cubit Royal Purple architecture and Grandma traversal remain unchanged.

## Next bound

B138 — measured baseline and independent negative controls. Stop at the first unverified empirical assertion.
