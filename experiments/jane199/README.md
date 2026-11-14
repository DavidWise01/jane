# JANE 199 — The Proxy That Pretends to Measure the Cause

**Natural invariant:** `Measured Proxy != Observed Cause`.

## Experiment

A fully recorded proxy is available for 16 synthetic beacon rounds. Only eight outcomes were measured; five of those eight are successes. Two constructed hidden-cause models match all measured outcomes and the same eight calibration records. Model A imputes zero for each missing outcome and gives 31.25% population prevalence. Model B imputes one for each missing outcome and gives 81.25%. Both have 100% proxy accuracy on the eight observed records. Model B's proxy is wrong on every unobserved record, which cannot be discovered from the recorded calibration alone.

`FLAY199.evaluate` retains both candidate constructions, the unmodified 16-row population, a SHA-256 frozen digest, explicitly synthetic calibration roots, missingness bounds of 31.25–81.25%, and a local SHA-256 hash-linked audit trail. It never declares causal identification.

## Run

```sh
python -W error -m unittest -q test_proxy.py
python proxy.py > result.json
```

The included regression suite has 41 tests. No external proxy, instrument, witness, active Jane runtime, or physical beacon is accessed; the tests check deterministic synthetic fixtures only. The local audit chain is not an externally anchored immutable ledger. Different model ancestry strings do not certify physical independence. No automatic learning or parent activation occurs.

## Viewer

Open `index.html` for the neon Canvas2D comparison. Switch between model A, B, or both and inspect how unchanged visible proxy data permits incompatible hidden outcomes.

## Next natural bound

**JANE 200 — The Validation Set That Was Chosen.** A proxy's validation sample may itself be selected conditional on outcomes. Independent calibration requires documented sampling frame, known inclusion mechanisms, and sealed provenance; selecting favorable validation cases is not proof of generalization.