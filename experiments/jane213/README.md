# JANE 213 — The Counter That Shared an Executor

**Invariant:** `Multiple Signed Witnesses != Independent Execution Evidence`.

FLAY 213 verifies signed executor and witness checkpoints using Ed25519 test keys, then traces declared `root`, `operator`, `sensor`, and `logging_service` ancestry. All witnesses must agree on task, sequence, nonce and counter head. Three distinct declared roots and operators plus two independently declared witness sensors are required. A shared logging service is withheld even with valid signatures. An append-only local SQLite hash chain and persisted nonce replay cache preserve evidence.

## Run

```sh
python -W error -m unittest -q test_custody.py
python custody.py > result.json
```

The experiment contains seven fixtures: independent declared custody; shared source root; shared operator; shared sensor; shared logging service; conflicting checkpoint; and impossible clock order. The regression suite has **28 tests**.

## Important limits

Every witness is simulated locally and all keys are deterministic **fixture-only secrets**. Do not reuse these keys for production. Signed declarations establish only *internal consistency*, not genuine physical custody, unlogged executor actions, observer independence, or a complete real-world event stream. GitHub and 0root.ai mirrors would be one corpus ancestry, not two independent witnesses. No Jane learning or automatic activation occurs.

## Next natural bound — JANE 214

**The Sensor That Was Replayed:** independent ownership labels do not prove that a witness observed a fresh event. Bind the sensor measurement to a challenge and preserve acquisition provenance.