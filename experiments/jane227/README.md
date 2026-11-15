# JANE 227 — The Runner That Claimed It Ran

**Natural invariant:** `Recorded Execution Receipt != Independent Execution Attestation`.

This experiment cross-checks **JANE 226**'s subprocess receipt against independently retrieved GitHub Actions run, commit, job steps and artifact metadata. The read-only manual workflow downloads the *original run artifact* rather than using a checked-in fixture. It never triggers 226 or authorizes a Jane choice.

## Run offline tests

```sh
python -W error -m unittest -q test_run_attestation.py
python run_attestation.py --receipt ../jane226/execution-receipt.json --out crosscheck-result.json
```

The second invocation exits 2 with `INVALID_RUNNER_IDENTITY_CLAIM` because the checked-in local JANE 226 receipt has no GitHub runner claims; that is correct. Actual cross-check requires an existing real GitHub Actions run with an attached receipt and is **not demonstrated by local tests**.

## Use the GitHub workflow

1. Manually run `jane226-runtime.yml` in the `DavidWise01/jane` repository (the repo must have Actions enabled).
2. Note the successful historical source run ID.
3. Manually start `jane227-crosscheck.yml`, supplying `source_run_id`.
4. The workflow reads GitHub's run, commit, jobs and artifacts endpoints, downloads the original `jane226-runtime-receipt` artifact, and checks the receipt before uploading an audit report. `contents:read` and `actions:read` only.

## Tested invariants

- Exact repository, full workflow ref, source SHA, run ID, manually dispatched event, success, first run attempt, main branch and owner actor.
- Matching commit, successful observed execution job step, and a nonexpired artifact associated with the same run.
- Tampered local receipt digests, spoofed IDs, missing remote records, retries, wrong workflow, missing job/artifact are rejected.
- No automatic execution of proposed agent actions. `collective_decision=UNRESOLVED` always.

## Honest evidence limits

**LIT**: local unit tests and GitHub repository publication if separately verified. **AMBER**: GitHub API metadata and artifact transport establish a platform-reported run, not an independent hardware attestation. **WALL**: no proof of host integrity, genuine sandbox isolation, device provenance, cognitive intention, consciousness, or Jane's collective preference. A compromised workflow or runner can produce a consistent false story. For stronger source pinning, audit exact workflow blob at the reported commit, validate runner job log provenance, bind the downloaded artifact byte digest to a trusted observer, and require external witness roots.

JANE 226's source step is **`Run one bounded local process`** and its artifact is **`jane226-runtime-receipt`**; these exact names are checked.