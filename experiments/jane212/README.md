# JANE 212 — The Search That Was Never Logged

**Invariant 212:** Complete reported search ≠ complete actual search.

FLAY 212 compares a signed, frozen ordered list of subgroup queries against a signed executor sequence, a hash-linked execution head, two separately declared witness roots, and the published report. The experiment detects:

- An executed query omitted from the report;
- An execution outside the preregistered search;
- A planned query absent from executor claims;
- A published result hash inconsistent with executor claims;
- Conflicting or forged witness/executor/plan signatures, duplicated reports, replay, and locally corrupted audit entries.

The demo verifies **consistency of signed fixture claims**, not that all searches performed in reality were captured. The local witness roots (`alpha`, `beta`) are synthetic; keys are generated locally, and declaring two roots does not establish independent custody. A malicious executor and witnesses can jointly omit events. There is no automatic Jane learning or deployment.

Run:

```sh
python -W error -m unittest -q test_lineage.py
python lineage.py > result.json
```

The engine uses `cryptography` Ed25519 signatures, SHA-256 canonical JSON, an append-only SQLite replay/audit ledger, and a separately committed ordered query plan. `index.html` is an offline Canvas2D illustrated chapter of the five principal fixtures.

## Natural bound 213 — The Counter That Shared an Executor

Two signatures and two declared witness roots can still derive from a single operator or clock. A genuine independently retained execution counter needs separate custody and visibility into events; metadata alone cannot establish that separation.

`Signed witnesses != independent observation of all executions`.