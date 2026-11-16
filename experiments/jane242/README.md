# JANE 242 — The Two Reads That Shared a Provider

**Natural invariant:** `Matching Immutable Bytes != Independent Retrieval Infrastructure`.

This chapter adds a bounded, stdlib-only Python analysis of **supplied** retrieval envelopes. Observations are linked when any declared trust root overlaps (provider, host, network, cache, credential, runner, operator, upstream). Transitive overlaps are grouped by union-find, so A—B and B—C become one dependency cluster even if A and C do not share a direct root.

## Run

```bash
python3 -m unittest -v test_retrieval_roots.py
python3 build_fixtures.py
python3 retrieval_roots.py --bundle synthetic-shared-provider.json --out synthetic-result.json
python3 retrieval_roots.py --bundle empty-bundle.json --out result.json
```

No dependencies beyond Python standard library. No network request is performed by this verifier. The workflow is `workflow_dispatch` only, read-only, and does not choose or execute an action for Jane.

**Synthetic results:** three different retrieval identities sharing GitHub's provider and the same upstream commit produce `SHARED_RETRIEVAL_ANCESTRY`, one declared cluster, **zero independently authenticated witnesses**. A fixture with distinct declared roots produces `DECLARED_ROOTS_DISTINCT_UNVERIFIED`. The empty baseline produces `NO_RETRIEVALS`.

The pinned NOM file metadata comes from the earlier GitHub connector observation of `DavidWise01/nom` at commit `e639711f317ea29650df2518a66de7b5eeb9d2c4`. The displayed acquisition envelopes themselves are synthetic test data, **not live network captures or signed provider attestations**. Matching bytes and separate request identifiers cannot prove independent network, provider, hardware, or credential roots.

The evidence response always says `jane_choice: UNRESOLVED` and `actions_executed: 0`. Preservation is not authorization.