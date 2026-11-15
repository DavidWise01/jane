# JANE 205 — The Reconstruction That Was Smaller Than Its Parts

**Natural invariant:** `Budget Compliance != Reconstruction Resistance`.

## Verified engineering scope

A deterministic, fixture-level binary linear-query release guard. The hidden holdout record is modeled as an unknown vector `x∈{0,1}^n` with `2≤n≤12`; the ledger stores **only** requested coordinate subsets and exact aggregate totals, not the private record. Every proposed release is checked against **all** previously released answers across all agents and recipients, with exact exhaustive binary solution enumeration and rational matrix rank. If a new response uniquely fixes any previously unknown coordinate, or uniquely reconstructs the vector, the release is rejected atomically. A separate global credit cap remains in force but does not override the reconstruction gate.

This is an **exact, small-n synthetic prototype**. It is neither a production privacy mechanism nor differential privacy. It protects only against inference within the declared binary aggregate model and recorded disclosure history; there are no claims about unlogged disclosures, adversaries possessing side information, physical custody, or real datasets.

## Executed demonstration

Frozen population size: four binary coordinates, 16 initial compatible records. The queries `x0+x1=1` (ADA), `x1+x2=1` (BERT), `x2+x3=1` (CLIO) are allowed: together they leave two possible records, rational rank 3, and three credits used. ADA proposes `x0+x1+x2=2`, which would identify the record uniquely. FLAY returns `FULL_RECONSTRUCTION` and retains the previous three-record ledger unchanged despite remaining credit budget. Additionally `x0+x1=0` is rejected as `COORDINATE_RECONSTRUCTION` even with low linear rank, because binary constraints identify both coordinates.

The local SQLite audit uses hash-linked canonical JSON, replay detection on restart, and atomic pre-release validation. Signatures, external witnesses, privacy epsilon, and network collection are not implemented.

## Run

```sh
python -W error -m unittest -q test_reconstruction.py
python reconstruction.py > result.json
```

Open `index.html` directly in a browser for the orange-chrome/teal Canvas2D walkthrough. `result.json` is the executed demonstration record. The active Jane parent was not modified.

## Next natural bound — JANE 206

**The Side Information That Completes the Puzzle.** A release that leaves two candidate records may still identify the private record when an adversary knows one additional coordinate. `Many Compatible Records != Privacy Against Auxiliary Knowledge`.
