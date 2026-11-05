# B167 — Independent repository authorization evidence

B166 can locate a retry intent and assess its commit provenance. B167 independently inspects a separate, opt-in, versioned `.formic/retry-authorization.json` declaration **from the same pinned default-branch head**. A valid approval declaration must match the exact intent digest, revision, prior PR and head SHA, specify one review-only action, and expire within seven days.

B167 also retrieves the **latest authorization-file-changing commit** and requires GitHub to report a verified commit attributed to `DavidWise01` as both author and committer, with the exact authorization-file blob SHA. It observes branch protection requiring administrator enforcement and at least one approving PR review. Missing GitHub permissions for branch protection return HOLD, not an optimistic PASS.

A valid policy is **evidence**, not independent authentication of human authorization. The only positive result is `POLICY_EVIDENCE_PRESENT`, with `mayCreatePR=false`, `mayRetry=false`, `mayMerge=false` and `mayWriteDefaultBranch=false`. A cooldown timer, green CI or GitHub-signed commit never transfers that authority.

This task is read-only: GET requests only, bounded to eight opted-in public repositories per run. No submitted code is executed. Actual opt-in approval files are not automatically installed in other repositories; the example is disabled.

Symbolic lattice preservation: `[a:122,b:122,c:122:d=a+b+c::isa]`; three witness sources a1,b1,c1 at one observation layer, `d` a derived view, zero defined ISA instructions, no votes or quorum.

## Next natural bound — B168
Create a **proof-carrying proposal envelope** that records exact diff, repository permission boundary, and expected checks. Only after explicit separately verified repository approval may a future draft-PR writer act. Do not auto-merge or silently reopen historical failures.
