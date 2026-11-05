# B169 — Fresh Repository Drift and Actual CI Evidence

**Natural bound:** a proof that was valid at creation time can become stale. B169 compares one B168 proof-carrying candidate to GitHub's **current** repository metadata, source branch and recorded CI evidence, using GET-only API requests.

## Checks
- Reject a proposal whose B168 audit does not PASS.
- Reject renamed, private, archived, forked, disabled or foreign repositories, or a changed default branch.
- Read the default branch SHA; compare it to the exact base SHA in the proposal. No tolerance for drift.
- Read the target path at that pinned SHA; if it exists or its absence cannot be established, HOLD.
- Query the base commit's GitHub check-runs **and** combined status contexts. Reject failures, cancellations, pending checks, missing check evidence, inaccessible endpoints and truncated results.
- Read the default-branch SHA **again** after checking evidence, and HOLD if it changed during the observation.
- The only positive state is `BASE_OBSERVED_PASS_NOT_PROPOSAL_VALIDATED`. That confirms *some reported checks on the existing base revision*, not tests of the unexecuted proposed diff.

B168 expected names such as `FORMIC_POLICY_GATE` are **expectations in the envelope**, not GitHub check names. B169 does not silently reclassify them as passed. The run never executes untrusted code or mutates a repository.

## Automation boundary

The B169 workflow runs native regression tests on relevant pushes, and can manually verify a *supplied, repository-committed* B168 proposal under `ecosystem/proposals/`. There is no live B168 proposal by default. Do not invent one or treat the B168 fixture as a genuine owner-issued authorization.

A proof may have integrity without authenticity; even the positive B169 state grants no write, retry, branch creation, PR, or merge permission. A future real permission stage must freshly verify actual repo-owner authorization and branch protection immediately before taking any action.

The symbolic diagram remains `[a:122,b:122,c:122:d=a+b+c::isa]`: a1, b1, c1 are independent source witnesses, d is read-only, observation depth 1, no quorum, zero defined ISA instructions.

## Next natural bound — B170
Compare *actual execution-time check plans* against a sandboxed patch evaluation with evidence of each executed check, without publishing credentials or equating base-branch CI success to proposal success.
