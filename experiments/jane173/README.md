# JANE 173 — The Witnesses Who Collude

**Invariant:** Authenticated agreement is not independent physical truth.

This experiment verifies Ed25519-signed measurement-source *claims* and a separate set of signed *acquisition vouchers*. Distinct signing keys do not count as independent measurements. Voucher roots are deduplicated by declared administrator and upstream ancestry. A forged, stale, replayed, or contradictory receipt is preserved as audit evidence and cannot certify physical independence.

Test: `python -m unittest -v test_collusion.py` (41 tests).

Demonstration: `python collusion.py`, output in `result.json`.

All keys and physical-source identifiers are deterministic **local fixtures**. The strongest success status is `CORROBORATED_FIXTURE_CLAIMS`: it means signed statements agree under a configured synthetic registry, **not** that a physical measurement, independently operated acquisition system, or real-world source identity has been verified. Hash-chain truncation requires an external retained head for detection. Jane's active parent remains frozen.

FLAY: `{{years.months.days}}{{hours.minutes.seconds}}{{degrees.arcminutes.arcseconds}}{{anchor}}`.

## Next natural bound: JANE 174 — The Acquisition That Must Be Reproducible
A signed acquisition voucher may itself be false. Require independently repeatable measurement procedures, raw capture commitments, and controls for shared instrument ancestry. Treat a claimed repeat measurement as new only when it can be independently reproduced.