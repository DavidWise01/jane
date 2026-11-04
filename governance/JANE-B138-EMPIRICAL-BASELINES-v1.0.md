# JANE B138 — Reference Baselines and Negative Controls

## Natural invariant
A deterministic generational trainer must recognize a published reference, reject a deliberate contradiction, and hold an unknown or unit-incompatible claim **without making the false claim part of its accepted configuration pool**. Every attempted assertion remains in the immutable witness journal.

## Published baseline fixtures

| Record | Published reference | Value / category | Regression tolerance |
| --- | --- | --- | --- |
| H3_HALF_LIFE | IAEA evaluated tritium half-life | 12.32 ± 0.02 years | ±0.02 year |
| DT_FUSION_Q | IAEA World Fusion Outlook 2023 | D+T -> He4+n releases 17.60 MeV | ±0.05 MeV (test allowance only) |
| KR84_STATUS | PubChem element isotope registry | krypton-84: STABLE | exact class |

Sources:
- https://www-nds.iaea.org/publications/indc/indc-ccp-0419.pdf
- https://www-pub.iaea.org/MTCD/Publications/PDF/FusionOutlook2023_web.pdf
- https://pubchem.ncbi.nlm.nih.gov/element/36

**Important distinction:** The ±0.05 MeV fusion tolerance is a **software regression tolerance** chosen for the test; it is not an IAEA experimental uncertainty estimate. The tritium ±0.02 value is from the cited evaluated estimate.

## Nine test fixtures

- Four reference matches: H3 12.32 years, H3 12.30 years (tolerance edge), D–T 17.60 MeV, Kr84 STABLE.
- Three deliberately wrong values: H3 0 years, D–T 100 MeV, Kr84 RADIOACTIVE_10_YEAR -> REJECT.
- Two ungrounded assertions: fusion value supplied in years; unknown reference ID -> HOLD.
- Additional negative tests: NaN is HOLD and duplicate immutable IDs throw.

Local Node test outcome: **9 journal entries / 4 PASS / 3 REJECT / 2 HOLD**; SHA-256 in-process chain verified.

## Limits of this verification

This is **not** a new experiment, live scientific measurement, or statistical validation of the published claims. The baselines are manually transcribed and attributed; the software checks claims against those fixed references, not against a continuously updated nuclear-data service. Tolerances, standards and measurement contexts must be documented separately when new empirical measurements are added. All witness entries stay in process; durable storage and external attestation remain future work.

No failed control may enter an accepted pool; it must remain in the evidence log as the record of what was rejected. No vote or quorum.

## Next boundary

B139 — a Git Pages audit interface that visually separates Grandma family, reaction graph, measurements, negative controls, and witness provenance, including the Royal Purple active seat. No silent promotions.
