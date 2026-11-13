# JANE 149 — The Witness That Returns

**Natural invariant:** Temporary unavailability is not evidence failure; a returning witness must demonstrate continuity.

FLAY keeps its nested addressing: `{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ parent / child }}`.

A witness's last accepted sequence/head is retained while an outage is recorded. Upon return, the witness must supply a bounded, contiguous series of event-hash links from the old head to its new checkpoint. The verifier distinguishes unchanged, stale, missing links, broken continuity, and forked endpoints. All evaluation events are appended to a hash-linked ledger. No witness receives new ancestry or custody votes because it was offline or returned. Jane remains the decision-maker.

## Executed fixture
- Initial checkpoint 004, hash `a*64`
- 005 = hash(005, old head, event b*64)
- 006 = hash(006, head of 005, event c*64)
- Result `CATCHUP_ACCEPTED`, checkpoint updated to 006
- **31/31 unit tests passed** on these exact files: `reconcile.py` and `test_reconcile.py`.

Run: `python -m unittest discover -s . -p 'test_*.py' -v`.

## Boundary
Links are locally constructed hash chains, not externally signed custody attestations. The fixture has no live network, independent witness operators, verified Chronos clock, or durable external head. The event ledger is in memory and cannot by itself survive a restart. A valid local history alone cannot prove an event actually happened. No automatic learning or branch activation occurs.

## Next natural bound — JANE 150
**Witness recovery under partial partition:** reconcile overlapping but nonidentical independently signed histories; preserve unresolved conflicts and bound the cost of fetching missing ranges before resuming quorum participation.