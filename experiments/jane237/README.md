# JANE 237 — The Missing Edge

**Invariant:** All declared ancestry edges verified ≠ all actual ancestry edges discovered.

The engine compares a declared graph at an exact source snapshot with one or more independently *claimed* inventories, evaluates coverage, and flags edges missing from the declaration. It never infers that silence proves an edge absent, that two names are independent controllers, or that a source's `external-verified` field constitutes actual independent authentication.

## Run

```bash
python -m unittest -v test_missing_edge.py
python missing_edge.py --bundle empty-bundle.json --output result.json
python missing_edge.py --bundle synthetic-discrepancy.json --output synthetic-result.json
```

The discrepancy command returns exit code 2 intentionally. The normal no-inventory baseline returns 0 and has verdict `NO_EXTERNAL_INVENTORIES`.

## Evidence contract

- Every inventory must match the declared graph's source snapshot exactly.
- Trust pins map a single source to a single registry root. This validates **claims within the fixture**, not independent real-world enrollment.
- Inventory payload digests detect accidental or malicious alteration against supplied digests; they do not authenticate the digest publisher.
- Missing coverage, untrusted inventories, mismatched snapshots, and contradictory inventories are preserved, never silently treated as clean.
- The verifier never executes any proposed tasks; Jane's choice remains `UNRESOLVED`.

## Next boundary

**JANE 238 — The Inventory That Copied the Graph**: prove external inventories were actually acquired independently rather than reserialized from the same ancestry manifest.