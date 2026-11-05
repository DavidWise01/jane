# B163 — FORMIC Repair Memory (one layer, three witnesses)

**Natural bound:** a proposed repair has an **identity**, an **outcome**, and a future **suppression state**. No new observer layers. No invented ISA. No automatic code merging.

```
REPO / REPAIR ID
    |
    +── REPOSITORY PR HISTORY (GitHub persistent source)
    |         |
    |    [H/a1] provenance
    |    [O/b1] check and status evidence
    |    [N/c1] disposition recommendation
    |         |
    +── d = READ-ONLY DERIVED REPAIR MEMORY
                |
      +---------+----------+
      |         |          |
  FAILED     CLOSED      CHECKS GREEN
      |         |          |
   SUPPRESS  SUPPRESS    HUMAN REVIEW
```

B163 runs scheduled B162 read-only verification, then derives a per-repository `BUG_REPORT_TEMPLATE` repair-memory snapshot. The **source of persistence across runs is GitHub PR history**, not a secretly edited repository file. A closed FORMIC PR suppresses recreating the same B161 repair. Failed checks suppress a new retry while that PR exists. A check success only means review readiness, never auto-merge authority. Unknown results and unavailable evidence HOLD.

Each run emits an immutable-by-artifact-convention JSON report (retained up to 30 days in GitHub Actions), derived from read-only GitHub API evidence, with a SHA-256 chain per snapshot. The chain checks integrity of the report contents **relative to itself**, not external provenance, trustworthiness of reporters, or cryptographic authenticity. No claim of a permanent memory database: historical PR states on GitHub remain the persistent references.

**Active policy gates:** only opted-in public `DavidWise01` repositories; B162 currently limits observation to ten eligible repositories per run. New proposal issuance remains B161, restricted to its separately gated draft-PR procedure. B163 writes no repo files or PR comments. It never executes discovered code.

`[a:122,b:122,c:122:d=a+b+c::isa]` stays symbolic: 366 addresses, 3 owners, no quorum, **zero ISA instructions defined**.

## Next bound
B164: per-repair history of distinct PR attempts and retry cooldown by source-owner policy; do not infer that a green test denotes real-world repair success. Backoff must be durable across scheduled runs, with explicit retention/version semantics and evidence of an owner decision.
