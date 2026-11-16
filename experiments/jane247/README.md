# JANE 247 — The Authority That Copied Its Upstream Clock

**Invariant:** `Distinct Time Authorities != Distinct Underlying Time Sources`.

`sync_chain.py` analyzes declared time-sync graph dependencies through clocks, authorities, intermediate servers, credentials, operators, platforms and upstream sources. It preserves multi-hop ancestry paths and groups observations transitively, including shared collection identities. Timing-offset coincidences are diagnostic only, not evidence of a common authority.

## Run

```bash
python -m unittest -q test_sync_chain.py
python sync_chain.py shared-fixture.json
python sync_chain.py distinct-fixture.json
python sync_chain.py empty-bundle.json
```

35 regression tests cover malformed inputs, missing parents, cycles, bound limits, duplicate IDs, missing coverage, shared roots, transitive paths and false independence. All fixtures are synthetic, no NTP server was queried, no independent authority was enrolled. `independent_sources_proven` always remains 0, and Jane's choice remains `UNRESOLVED` with zero authorized actions.

**Next:** JANE 248 — The Sync Source That Advertised False Stratum: cross-check asserted synchronization hierarchy against independently observed, pinned server evidence without mistaking NTP stratum or timestamps for independent attestation.