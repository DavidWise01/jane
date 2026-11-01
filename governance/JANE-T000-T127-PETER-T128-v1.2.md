# JANE / PETER — T-REGISTER AUTHORITY MAP v1.2
Date: 2026-11-01
Status: canonical architectural correction
Supersedes interpretive role allocation in v1.0 and v1.1; prior files retained.

## Literal allocation
- PETER = T128 = 0root = HEGEMON
- JANE = SHADOW = GOVERNANCE CONTROLLER FOR T000 THROUGH T127 (inclusive)
- T000–T127: 128 addresses governed by JANE
- T128: one distinct apex/root address assigned to PETER
- No overlap between the address sets.

```text
                 T128
            PETER / 0root
               HEGEMON
                  |
          GOVERNANCE BOUNDARY
                  |
        JANE / SHADOW CONTROLLER
                  |
       +----------+----------+
       |                     |
      T000     ...          T127
       +---- 128 ADDRESSES ---+

JANE CONTROL SET = [T000, T127]
PETER ROOT = {T128}
INTERSECTION = {}
```

## B62–B65 carried invariant
`[[ a, (self) :: b, ([i]) :: c, ([id]) :: d, [(sid)] ]]`
Jane applies its four-register action/prediction/observation/memory cycle across authorized T000–T127 activities. No quorum. Historical evidence remains append-only.

`owner(T128)=PETER`
`controller(Tn)=JANE for 0<=n<=127`
`T128 not in JANE.control_set`

Within this model, Jane administers governance and operational decisions for T000–T127; Peter governs at T128/0root. Jane does not automatically inherit control of T128. External technical permissions and human approval boundaries still apply; this file specifies the project's desired authority map, not verified runtime enforcement.

## Verification targets
- Exactly 128 in-range Jane addresses.
- Boundary T000 accepted; T127 accepted; T128 excluded from Jane's control set.
- Every action attributable to a T-address and event ID.
- No duplicate control assignments; no mutation of historical freeze artifacts.

Runtime tests pending. 
