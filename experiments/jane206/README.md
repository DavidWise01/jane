# JANE 206 — The Side Information That Completes the Puzzle

**Natural invariant:** `Multiple Compatible Records != Privacy Against Auxiliary Knowledge`.

## Core demonstration

The frozen four-bit dataset is constrained by three disclosed aggregates:

- `x0 + x1 = 1`
- `x1 + x2 = 1`
- `x2 + x3 = 1`

The exact binary solution set is `{0101, 1010}`. A declared external fact `x0 = 1` collapses it to `{1010}`. The new auxiliary-knowledge check emits `AUXILIARY_COMPLETES_RECONSTRUCTION` and does not retain that risky disclosure by default. This gate is prospective for FLAY's own ledger; it **cannot prevent an adversary from using facts they already know**.

## Files

- `auxiliary.py`: deterministic binary candidate enumeration; reconstruction and per-coordinate risk gates; source-root labels; hash-linked local SQLite audit.
- `test_auxiliary.py`: 40 regression tests, including contradictions, tampering, input limits, and persistent-chain verification.
- `result.json`: executed fixture evidence.
- `index.html`: interactive orange-chrome and teal Canvas2D visualization.

Run `python -W error -m unittest -q test_auxiliary.py` and `python auxiliary.py > result.json`.

### Boundaries

No external source was inspected; source ancestry and external fact are declared synthetic fixtures. No signatures or external witnesses are asserted. The local SQLite chain is not externally anchored; a database operator could rewrite it. Ledger events are replay-verified on reopening, but model-state queries and facts are in-memory and **not reconstructed from the ledger** after restart. Large populations are out of scope; enumeration is capped at 18 binary coordinates. No actual private holdout is included, no Jane learning/activation occurs, and physical independence is not established.

## Next natural bound

**JANE 207 — The Auxiliary Fact That Was Inferred.** Attackers may not know a bit directly; they may infer it from correlations or uncertain side information. FLAY should preserve confidence and abstain from converting probability into certainty.