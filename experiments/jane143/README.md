# JANE 143 — The Observation That Changes the Answer

**Invariant:** A received observation is not verified knowledge.

Canonical FLAY addressing:

```
{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ parent / child }}
```

## Implementation

The locally tested `outcome.py` implements Ed25519 receipt signing and verification, strict case binding, Chronos UTC-offset checks, locally supplied custody roots and checkpoint heads, replay detection, explicit conflict quarantine, append-only ACCEPT/REJECT/EVALUATE audit events, and recalculation of correlated parent/child risk bounds.

The original unknown case is never rewritten. A derived view reports RESOLVED only after three distinct, configured custody roots submit matching signed claims. Any valid contradictory claim triggers CONFLICT and blocks use of the apparent quorum. Rejected or conflicting inputs remain audit events. The immutable frozen parent remains active; no learning is applied.

## Reproducible fixture

Eight cases: six routine known; two critical unknown; both critical candidates cost 50 if wrong. Original parent risk [12,112] and candidate [0,100], change [-112,88]. The fixture then signs three receipts each for C0=False and C1=False with ephemeral local keys. Once C0 resolves, parent [62,112], child [0,50], change [-112,-12]; FLAY still holds because of the critical cohort budget of 0. After C1 also resolves, parent [112,112], child [0,0], change [-112,-112], `JANE_REVIEW_CANDIDATE`. Jane remains undecided.

All **52/52 local tests passed** on the attached source and test suite. Run `python -m pip install cryptography && cd jane143 && python -m unittest -v`.

## Boundaries

The generated fixture keys and trusted custody roots **do not represent independently operated witnesses**, even though the Ed25519 signature checks are real. Claimed case labels are synthetic and cannot prove a real-world outcome. The checkpoint map is supplied rather than fetched from authenticated remote custody. Replay state is process-local, so production needs persistent storage. The hash ledger needs an externally retained head to detect clean truncation. Chronos is a signed claim with UTC offset, not trusted hardware time. Truth is not guaranteed by quorum agreement. No autonomous learning or real-world deployment occurred.

## Next bound — JANE 144

Evidence provenance continuity across reboot: persist receipt nonces and quorum state; detect custody equivocation across successive checkpoints; distinguish consensus on a claim from corroboration of the underlying observation.