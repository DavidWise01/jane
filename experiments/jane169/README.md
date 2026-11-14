# JANE 169 — The Clock Under Changing Conditions

**Invariant:** A change to operating conditions requires reconsidering the calibration assumptions before the clock can keep being treated as calibrated.

The Python engine `conditions.py` models condition profiles `{temperature, power, sync}` and a separate declared drift policy (`ppm`, maximum age, maximum uncertainty). When a known profile changes, its conservative transition budget uses the **maximum of the two profile rates over the entire unknown transition interval**. It never resets accumulated uncertainty on a profile switch. Sudden clock-offset jumps and expired calibration are rejected and preserved as `HOLD` events in a hash-linked local ledger.

Unknown profiles produce `UNKNOWN_CONDITION`, an **unbounded uncertainty** output (represented as null), and require new calibration; returning to a known profile does not automatically restore confidence. An explicit `calibrate` call requires an external evidence digest *label* but does not itself authenticate those references. External anchoring of the hash head is needed to detect clean truncation.

All profiles, clocks, and readings are **synthetic deterministic fixtures**. No physical sensors, independent time authorities, signed telemetry, deployed scheduler, or independent witness network were connected. The rate policy is assumed, not scientifically measured. Known-profile labels and claimed drift rates must be authenticated and validated before production use.

Run in directory: `python -m unittest -v test_conditions.py` (41 tests); `python conditions.py` (deterministic evidence output).

## Reproduction

- Start in normal/mains/locked, claimed drift 20 ppm, baseline uncertainty ±2 ms.
- After 10 s, offset +1 ms, uncertainty ±3 ms: `WITHIN_PROFILE`.
- Switch to hot/battery/holdover (100 ppm) by 20 s, uncertainty ±4 ms: `CONDITION_CHANGE_ACCEPTED`.
- At 21 s, offset +50 ms exceeds ±5 ms envelope: `CLOCK_JUMP`.
- Separately, switch to unknown/battery/holdover: `UNKNOWN_CONDITION`, uncertainty becomes unbounded until recalibration.

## Next natural bound — JANE 170

**Authenticating the condition itself.** A claimed operating profile can be fabricated. Condition labels and policy transitions need signed provenance; missing sensor readings or conflicting observations must not inherit the most convenient drift rate.