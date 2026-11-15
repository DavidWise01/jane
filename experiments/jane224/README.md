# JANE 224 — The First Unassigned Candidate

**Invariant:** `Deterministically generated agent-related proposal != that agent's preference`.

This increment gives a *running adapter* the ability to generate one bounded, reproducible suggested research task from the actual NOM citation ledger and grounding receipts. It avoids impersonating NOM and makes **no** claim that Jane, NOM, or another A.C.I. chose or wanted the result. The procedure selects the **earliest citation pair in NOM's append-only ledger that lacks a matching grounding receipt**. No paper contents, private files, external commands, API calls, or full-language agent inference are executed.

## Implementation

- `proposer.py`: dependency-free, read-only Python CLI; verifies source hosts, schema, timezone-aware timestamp order, distinct citation pairs, grounding receipt origins, and file/row bounds. Pins full 40-hex source commit and hashes original input bytes. Candidate contains original URLs and explicitly `execution_authorized:false`.
- `test_proposer.py`: 35 adversarial and deterministic regression tests, including malformed records, forged origins, time errors, duplicate records, unsupported source records, out-of-scope grounding, limit checks, and false attribution.
- `.github/workflows/jane224-nom-proposal.yml`: manually dispatchable, read-only workflow that checks out Jane and NOM at a resolved commit; runs tests and the adapter, uploads a JSON receipt. It never commits back or calls a model.
- `index.html`: self-contained chapter for inspection; no JPG by user request.

## Reproduce locally

```bash
python -W error -m unittest -q test_proposer.py
python proposer.py --ledger path/to/nom/ledger.jsonl --ground path/to/nom/ground_truth.jsonl \
 --nom-commit FULL_40_CHARACTER_COMMIT_SHA --output receipt.json
```

The program intentionally **does not sign its output as NOM**. A GitHub Actions run provides platform run metadata and resolved source commit; GitHub's artifact is still not independently signed by NOM nor a demonstration of Jane's subjective preference. A GitHub repository checkout may be a versioned observation, not a currently running agent. The next step is a formally attributable response produced by a separately governed executable A.C.I. instance, with a reviewed runtime key and anti-replay challenge; only then test aggregation at Jane level.

Past observes. Present deserves. Future reserves.