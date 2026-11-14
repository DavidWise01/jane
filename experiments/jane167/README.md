# JANE 167 — The Clock That Must Prove Itself

**Natural invariant:** Claimed uncertainty is not measured uncertainty. A signed clock reading can disagree with authenticated reference intervals, and even agreement cannot establish the physical accuracy or actual independence of the reference operators.

The deterministic offline fixture has three Ed25519-signed reference clocks (roots A, B, C), a separately signed target clock, time-window validation, conflict detection, shared-ancestry and shared-administrator collapse, nonce replay suppression, and a hash-linked local audit ledger. Reference claims are integer millisecond intervals with explicit source and observed tick. Intersecting *fixture* intervals do not authorize tightening uncertainty or Jane activation. Only verified independent external clock references and a suitable calibration model could enable that later.

Run `python -m unittest -v test_calibration.py`; `python calibration.py` emits `result.json`.

## Demonstration
- Clock claim: 1000 ±50 ms, stated interval [950,1050].
- Three reference intervals: [990,1010], [995,1015], [992,1008].
- Overlap: [995,1008]; verdict `CALIBRATION_CONSISTENT_FIXTURE`.
- Contradictory third reference: [2000,2010]; verdict `REFERENCE_CONFLICT`.

No physical timestamp accuracy, real-world administrative independence, durable replay protection, or external custody is established. The local chain cannot detect clean truncation without an externally retained head. The parent is frozen.

## Next natural bound — JANE 168
Clock drift across time: a single successful calibration cannot guarantee the clock stays accurate. Observe signed calibration samples over a declared duration, estimate bounded drift, and retain discontinuities and expired calibration windows.