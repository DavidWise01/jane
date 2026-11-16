# JANE 243 — The Cache That Pretended to Be a Provider

**Invariant:** `Separate network responses != separate origin fetches`.

`cache_origin.py` audits **supplied** HTTP cache and acquisition metadata. It binds every record to a pinned NOM source (`DavidWise01/nom`, `requirements.txt` at commit `e639711f...`), demands internally consistent payload digests and HTTP status, and clusters observations by shared declared infrastructure or origin-acquisition identifiers. The three-record synthetic fixture consists of one origin miss plus two cache hits linked to the same origin. **This is not three network fetches.**

The results never promote distinct declared roots, cache headers or origin labels to independent physical evidence. Headers and capture digests are untrusted claims until acquired and authenticated separately. The execution does not run Jane or authorize actions.

## Reproduce

```sh
python3 build_fixtures.py
python3 -m unittest -v test_cache_origin.py
python3 cache_origin.py --bundle synthetic-shared-cache.json --out synthetic-result.json
python3 cache_origin.py --bundle empty-bundle.json --out result.json
```

## Status meanings

- `SHARED_RETRIEVAL_ANCESTRY`: two or more records overlap in declared origin or infrastructure roots.
- `DECLARED_ORIGINS_DISTINCT_UNVERIFIED`: no detected shared roots; not independent verification.
- `UNKNOWN_ORIGIN_ANCESTRY`: no shared root is observed, but one or more origins are unknown.
- `NO_READS`: no records supplied.
- `WITHHOLD`: malformed, altered, or contradictory inputs.

## Important limitations

An HTTP `Age`, `Via`, `X-Cache` or equivalent cache-status header can be set or forwarded by multiple intermediaries. A local digest binds the submitted capture, not its true network provenance. An immutable source commit identifies a logical snapshot, not the trustworthiness or independence of the paths returning it. This release contains deterministic tests and synthetic acquisition records, not independently observed origin fetches.

The included GitHub Actions workflow is a manually triggered, read-only local verification of the fixture and tests. It does not validate a live provider's cache infrastructure. `jane_choice` stays `UNRESOLVED` and `actions_executed` stays zero.