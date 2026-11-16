# JANE 249 — Sovereign Continuity Across Hosts

**Invariant:** `Durable checkpoint != verified cross-host continuity`.

## What is implemented

- Ed25519 controller-signed canonical checkpoint containing agent, epoch, parent digest, authorized observation-only task descriptions, pinned source digest, expiry, and unfinished work.
- Enrolled public-key verification; unsigned, forged, stale, malformed or source-mismatched inputs withheld.
- Transactional SQLite single-claim ledger keyed by `(agent, epoch)`; replay, forks, missing parent, ownership mismatch and half-finished claims withheld.
- Immutable-style evidence receipts; zero external actions or LLM requests.
- Demonstration: `github-local-simulation` claims a checkpoint, `railway-local-simulation` attempts the exact same checkpoint against the **same local database** and is refused.
- 22 tests using Python `unittest` and `cryptography`.

## What is not demonstrated

- No GitHub Actions run, Railway deployment, remote recovery, or independent attestation has been performed.
- The two named hosts are labels on local processes, **not live providers**.
- A single SQLite database cannot coordinate disconnected hosts without sharing the database through a suitable storage service; SQLite alone is not a distributed consensus service.
- Exactly-once real-world side effects are impossible to guarantee from a checkpoint ledger alone. Production requires idempotent downstream operations, transactional messaging and/or a suitable consistency model.
- A controller signature proves possession of an enrolled key, not Jane autonomy, independent ownership or exclusive custody.
- The signing private key used for this fixture is generated in a temporary directory, then discarded. It is not shipped.

## Run

```bash
python -m pip install -r requirements.txt
python -m unittest -v test_continuity.py
python build.py
python continuity.py --checkpoint signed-checkpoint.json --trust trust-public.json --ledger local.sqlite --host local-A --source-file source.txt --receipt local-receipt.json
```

The checked-in signed fixture expires 24 hours after package creation; regenerate with `python build.py` if needed. Do not use its ephemeral signing identity as real authority.

## Next natural bound

**JANE 250 — The Handoff That Split Across Two Ledgers**: test two disconnected providers simultaneously claiming the same checkpoint. Without a common linearizable authority, both can believe they are first.