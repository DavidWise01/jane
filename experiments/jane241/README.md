# JANE 241 — The Provider That Changed Between Reads

**Invariant:** Two successful fetches do not establish one consistent snapshot.

`toctou.py` compares checked and consumed content against a pinned 40-character commit SHA, SHA-256 and Git blob SHA-1. It explicitly refuses mutable `main` refs, reused retrieval identifiers, altered bytes or source revision mismatch. All outcomes preserve `jane_choice=UNRESOLVED`, `actions_executed=0`.

`fetch_twice.py` issues two separate, bounded requests to GitHub's Contents API. Both use the *same pinned commit* and GitHub trust root. The Contents API does not separately attest `resolved_commit`; it is populated from the caller's pinned request. This is not hardware attestation nor independent provider corroboration. The checked/used JSON fixtures are demonstrations constructed from NOM bytes observed through the GitHub connector, not proof of live independent retrieval.

## Run

```sh
python -m unittest discover -v
python toctou.py --claim claim.json --out result.json # expects exit code 2 (no observations)
python toctou.py --claim claim.json --check checked-fixture.json --use used-fixture.json --out fixture-result.json
python fetch_twice.py --claim claim.json --out live-result.json # network required
```

The manual `.github/workflows/jane241-check-use.yml` runs tests and live requests with read-only repository permission and uploads a receipt. No writes to external sources or collective choices are authorized. The workflow must be triggered separately; publishing it does not execute it.