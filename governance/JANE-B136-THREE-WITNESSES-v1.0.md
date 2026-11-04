# JANE B136 — Contradictory Witnesses; No Quorum

## Natural invariant

Three independent observations are **three reports**, not three votes. There is no majority, no quorum and no compelled agreement. Preserve what each witness actually observed. A conflict means **HOLD** for an unwarranted promotion and investigation of the difference, not deletion of the dissenting report.

## Structure

```text
                    ONE EVENT
             a1          b1          c1
             |           |           |
          [l,v,u]     [l,v,u]      [l,v,u]
             |           |           |
             +-----------+-----------+
                         |
       check event identity, units, independence
       and interval compatibility (not vote count)
                         |
           +-------------+--------------+
           |                            |
      COMPATIBLE                    INCOMPATIBLE
           |                            |
      check separate                 HOLD
      evidence approval           append mismatch
           |
      ELIGIBLE FOR NEXT GATE
       (NOT proof or PROMOTE)
```

All reports include an immutable observation ID, event ID, exact witness channel a1/b1/c1, source, measured metric, unit, reported lower/value/upper interval, and independence status. The comparison uses the **latest appended observation from each named witness** for one event, leaving all earlier observations intact.

**Outcomes:** Missing witness report, differing metrics/units, unestablished independence, or non-overlapping intervals → HOLD. Even where reports are compatible, the outcome remains HOLD until an explicitly supplied separate external evidence gate is approved; only then the record becomes ELIGIBLE_FOR_NEXT_GATE.

Agreement among overlapping intervals is not validation of underlying truth or statistical independence. Evidence approval in this deterministic test is a caller-supplied boolean, not independent verification of physical evidence. The programme cannot infer independent instrumentation or detect coordinated manipulation.

## Test

Local Node.js test passed with seven immutable observations:
1. A1 alone → HOLD, missing b1/c1.
2. B1 and C1 added → intervals overlap, but still HOLD until external evidence gate.
3. Separate evidence gate supplied → ELIGIBLE_FOR_NEXT_GATE, not automatic promotion.
4. B2 contradictory → HOLD.
5. B3 independence unestablished → HOLD.
6. B4 revised compatible, independent observation → eligible again if evidence approved.
7. C2 incompatible unit → HOLD.

Negative tests check duplicate immutable ID and invalid intervals. In-memory SHA-256 hash-chained journal verified. Persistence outside process, cryptographic identity of witnesses, genuine independence and laboratory truth are **not** established.

## Next

B137: evaluated isotope completeness and physically evidenced reaction graph with unsupported transitions marked UNKNOWN rather than guessed.

Historical B117–B135, 16-cortex Royal Purple active seat, and two analytical cubits are unchanged.
