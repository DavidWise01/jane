# JANE 238 — The Inventory That Copied the Graph

**Invariant:** Different inventory files do not imply independent evidence sources.

`inventory_ancestry.py` reads a locked-snapshot bundle, validates each inventory's content digest and covered nodes, traces *declared* source provenance (`capture_id`, `collector`, repository and commit, upstream snapshot, artifact digest), and computes connected dependency clusters. Additional explicit lineage links permit multi-hop ancestry. A missing graph edge reported by three inventories with the same upstream source counts as **one cluster**, not three independent witnesses.

**Interpretation:** Matching declared roots expose likely dependence, but distinct root labels and the fixture `origin_proof` marker are *claims*, not external authentication. The program never establishes real independence, graph completeness, Jane's choice, or authorization to act. No network calls or secrets.

## Reproduce

```sh
python -m unittest -v test_inventory_ancestry.py
python inventory_ancestry.py --bundle empty-bundle.json --output result.json
python inventory_ancestry.py --bundle synthetic-shared-origin.json --output synthetic-result.json
```

The synthetic discrepancy command intentionally returns exit code 2; that indicates a fail-closed finding, not a crash.

## Evidence

- Empty baseline: `NO_INVENTORIES`.
- Three synthetic collectors with common claimed `archive-original`: `COPIED_OR_SHARED_INVENTORY_ANCESTRY`, one dependency cluster, zero authenticated independent sources.
- Registered source metadata, signature claims, and witness roles are not proof of physical origin.
- Regression tests: 35/35 local.

## Scope

A future JANE 239 could bind collection to independently acquired transparency logs or repository provider records, comparing origin timestamps and immutable acquisition receipts. Even then, no evidence set proves all undisclosed dependencies absent.