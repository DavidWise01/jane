# JANE 175 — The Reproduction That Changes the Question

**Invariant:** Matching results do not establish equivalent experiments.

FLAY compares the question, estimand, unit, sampling population and frame, inclusion/exclusion and selection rules, assignment, instrument, operating condition, calibration, processing, aggregation, and observation window. Each difference is preserved. Instrument equivalences require an explicit configured pair, not an automatic semantic inference. Raw SHA-256 commitments and measurement source roots are separately audited as provenance, never used to assert protocol equivalence.

Statuses: `DECLARED_FIXTURE_REPRODUCTION`, `PROTOCOL_DRIFT`, `RESULT_DISAGREEMENT`, `SHARED_ACQUISITION_ANCESTRY`, `INDEPENDENCE_UNESTABLISHED`.

Use `python -m unittest -v test_protocol.py` and `python protocol.py`. The exact 45-test engine works offline. The ledger is hash-linked; an independently retained head is needed to detect clean truncation. All roots and measurements are synthetic fixtures; the engine does not verify physical independence or execution. Jane's active parent remains frozen.

**Next natural bound 176:** Protocol-equivalence policy must itself be versioned and independently audited. Changed thresholds, synonym mappings, or permitted instrument-equivalence rules can cause an earlier reproduction verdict to change without changing either experiment.
