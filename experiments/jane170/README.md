# JANE 170 — The Sensor That Can Lie

**Invariant:** reported condition ≠ verified condition. A drift bound requires fresh, authenticated sensor observations, checked custody provenance, and agreement under the declared quorum. Any conflict, unknown profile, changed expected profile, or insufficient evidence must force recalibration instead of choosing the most favorable drift allowance.

## Executable contract

- Each observation is domain-separated and Ed25519-signed by a configured sensor key.
- The signed body carries sensor ID, declared custody root, administrator, condition, observation clock, timestamp, uncertainty and nonce.
- Accepted nonces persist in SQLite across verifier restarts. The local audit ledger is hash-linked.
- Three distinct *configured* administrative roots must agree on one supported profile for the drift allowance to be returned.
- Contradictory reports, unknown conditions, expiry, future skew, invalid signatures, replay, or duplicated administrative ancestry are preserved and withhold a drift allowance.
- None of the synthetic fixture signers constitute real-world independently verified operators. A correctly signed report does not establish physical sensor truth; the ledger needs an externally held head to resist clean suffix deletion.
- Jane's active parent remains frozen; no learning or operational permission is granted.

## Local run

```sh
python -m unittest -v test_sensors.py
python sensors.py > result.json
```

**Fixture drift rates:** normal 10 ppm, hot battery 120 ppm, holdover 250 ppm. These numbers are experiment inputs, not hardware calibration values.

## Next natural bound — JANE 171

**Provenance of provenance:** cross-check whether nominally different sensor administrators rely on a shared physical sensor, firmware stack, clock, or data broker. Distinct signing keys and labels must not inflate source diversity.