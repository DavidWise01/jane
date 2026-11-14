# JANE 202 — The Test That Leaked Through a Summary

**Natural invariant:** `No Raw Test Access != No Test Information Leakage`.

`leakage.py` implements an append-only hash-linked **synthetic event log**, with a directed information lineage graph. It tracks `seal`, `evaluation`, `score`, `summary`, `embedding`, `report`, `transfer`, `selection`, `finalize`, and `declassify` events. The ancestry of a sealed dataset follows derived artifacts across actors; a downstream selection linked to the sealed test is classified as `SEALED_INFORMATION_INFLUENCED_SELECTION`. Information observed but with no recorded path to a decision is classified `INDIRECT_EXPOSURE_NO_SELECTION_PATH`. No recorded exposure is not proof of no exposure.

The engine rejects repeated IDs, broken parents, non-monotonic epochs, malformed events, and modified hash-linked records. It does **not** cryptographically authenticate actors or prove chronology, complete disclosure, independent custody, or actual execution. This is an explicitly synthetic demonstration.

## Reproduce

```bash
python -W error -m unittest -q test_leakage.py
python leakage.py > result.json
```

All **41** tests passed locally. `result.json` retains six scenarios and the recorded ancestry of each disclosure and model-selection decision.

Open `index.html` for the interactive high-definition neon Canvas2D lineage view. No dependencies or network access are needed for the viewer.

The original Jane model remains frozen. There is no automatic training, updating, or activation.

## Next natural bound — JANE 203

**The Summary That Was Queried Adaptively.** Even a low-bandwidth aggregate result can reveal significant test information when a developer asks a sequence of related questions. Track the total disclosure budget and adaptive query history rather than classifying each summary in isolation.