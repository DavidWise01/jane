# JANE 218 — The Sensor That Simulated the Stimulus

**Natural invariant:** `Valid Response Attestation != Independent Physical Measurement`.

## What was executed

`instrument.py` audits a signed fixture challenge, signed executor result, and separately signed acquisition claims. It cross-checks challenge nonce, stimulus content commitment, capture timing, content hash, capture IDs, and declared sensor, root, operator, and service ancestry. It requires at least two distinct **declared external instrument** observations. If both witnesses are software-only it withholds the physical-measurement claim. **Even its successful verdict is `DECLARED_INSTRUMENT_CONSISTENCY_FIXTURE`, never a claim of actual hardware capture.**

A persistent local SQLite ledger rejects reused challenge nonces after restart. The deterministic Ed25519 keys are synthetic fixture keys and not independent trusted hardware identities. Metadata labels alone cannot establish real instrument integrity, observation secrecy, or physical causation. No live sensor or public beacon was contacted. Jane's active parent was not modified.

## Tests

```sh
python -m pip install cryptography
python -W error -m unittest -q test_instrument.py
python instrument.py > result.json
```

36 regression tests cover signatures, role binding, challenge chronology, mismatched content, duplicate capture IDs, reused challenges, SQLite restart, sensor/operator/service/root ancestry, simulated-only evidence, an insufficient number of external claims, and preservation of the fixture-only boundary.

## Interactive chapter

Open `index.html` locally or under GitHub Pages. Select one of six fixtures to see their verdicts in the orange/chrome/teal Canvas2D observation diagram.

## Next natural bound — JANE 219: The Instrument That Attested to Itself

A purported external instrument can sign its own fictitious measurement. Bind the instrument's identity and firmware claims to independently retained enrollment evidence; preserve the impossibility of proving physical trust from self-signed software metadata alone.