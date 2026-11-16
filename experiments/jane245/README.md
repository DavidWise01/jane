# JANE 245 — The Clock That Certified Its Own Time

**Invariant:** `Consistent timestamps != trusted time`.

The verifier requires three Ed25519-signed clock statements over the exact canonical event digest and challenge. It checks enrolled public keys, revocation, distinct declared controller/platform/source roots, bounded clock uncertainty, a non-empty intersection of time intervals, and the maximum possible age of the provider's declared acquisition time.

**This is NOT a secure time oracle.** Three generated fixture keys are public test-only keys, not real independent clock services. Signed statements cannot establish that the time was correct, that infrastructure is truly independent, or that acquisition happened when the provider claims. The origin clock must be separately authenticated for real freshness evidence. Never deploy with the included deterministic test keys.

## Run

```bash
python -m pip install -r requirements.txt
python -m unittest -v test_trusted_time.py
python trusted_time.py --bundle signed-fixture.json --registry registry.json --output /tmp/jane245-signed.json
python trusted_time.py --bundle stale-fixture.json --registry registry.json --output /tmp/jane245-stale.json
python trusted_time.py --bundle empty-bundle.json --registry registry.json --output /tmp/jane245-empty.json
```

Rebuild fixtures using `python make_fixtures.py` (test-only). `result.json` is the empty runtime baseline. No live authenticated time witnesses were contacted. Jane's choice remains `UNRESOLVED`, with zero actions executed.

A time authority needs a separate authenticated enrollment, an independent trusted time source, freshness challenge issuance, immutable observation and no shared platform/controller roots. Merely obtaining multiple HTTP Date headers is insufficient.

The manual GitHub workflow runs local tests and fixtures; passing it does not attest physical time or independent execution.