# JANE 144 — The Witness That Remembers

FLAY's time and structure address is preserved:

```
{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ custody / key generation / witness }}
```

## Implemented

- Ed25519 verifies signed outcome receipts and signed key rotations.
- SQLite retains custody-root nonces and claims across process restarts.
- New signing keys inherit the original custodian's vote; rotation cannot multiply witness independence.
- Contradictory signed claims by one custody root are marked `EQUIVOCATION`; contradicting roots are `CONFLICT`.
- At least three configured distinct custody roots must agree to resolve a claimed outcome.
- Events form a hash chain. An externally retained (but local fixture) head detects rollback to a valid earlier database state.
- Jane stays `UNDECIDED`; no active rule changes.

## Verification

The full `witness.py` and `test_witness.py` were executed together with **24 of 24 tests passing** using Python and `cryptography 46.0.4`.

```bash
python -m pip install cryptography
python -m unittest discover -s . -p 'test_*.py' -v
```

## Boundaries

This experiment uses an ordinary local external anchor file, not an actually separate administrative service. If an attacker can replace both the database and its external head, rollback may go undetected. Custody mappings and trust keys are synthetic fixtures, not externally verified identities. Chronos's clock is not authenticated. The SQLite ledger does not provide tamper-resistant or distributed consensus guarantees. A successful resolution is agreement by locally configured keys, not independently established ground truth.

## JANE 145 — Natural bound

Witness custody must leave the laboratory: independently administered anchor stores, replicated nonces and conflict gossip, plus a verifiable recovery protocol when one custodian is offline or dishonest.