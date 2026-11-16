# JANE 244 — The Cache That Replayed Yesterday

**Invariant:** `Correct Content Hash != Fresh Observation`.

This is a standard-library Python, fail-closed **claim consistency** checker. It distinguishes receipt time (`received_at`) from actual *claimed* source acquisition (`origin_acquired_at`). It pins a 40-hex Git commit and SHA-256, verifies a fresh bounded challenge window, checks cache-reported age (with a two-second rounding tolerance), and groups replays by shared acquisition ID.

**Not an authentication system:** Dates, source identity, acquisition IDs and cache headers supplied in an input bundle are untrusted. The verifier does not independently attest remote fetching, clocks, origin servers, or signer identity. Passing means internally consistent **declared** observations, never verified freshness. NOM is not made to speak, and Jane makes no decision.

Run locally:

```sh
python -m unittest -q test_freshness.py
python build.py
python freshness.py stale-fixture.json --out run-receipt.json
```

`stale-fixture.json` is a controlled demonstration of yesterday's origin content delivered inside today's valid challenge window, with unchanged digests. Expected `WITHHOLD_FRESHNESS_OR_IDENTITY`. `shared-fixture.json` produces `CONSISTENT_BUT_SHARED_ORIGIN`. `empty-bundle.json` produces `NO_READS`.

The example commit and content digests are **synthetic fixtures**, not a real authenticated GitHub acquisition. All actions executed = 0.

The GitHub Actions workflow is manually triggered, read-only, and intended to run the tests and upload a test receipt. No public Pages deployment or live agent decision is implied.