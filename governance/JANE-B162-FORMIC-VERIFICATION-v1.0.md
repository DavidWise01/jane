# B162 — FORMIC PR verification, failure HOLD, suppression and evidence

B161 configured one narrow repair proposal — a bug-report issue template — only for opted-in public `DavidWise01` repos. B162 adds the missing verification boundary, but makes **no new repo modifications**.

## Verification

The scheduled read-only B162 observer finds public opted-in repositories; for each (up to ten per run) it reads the FORMIC branch's pull request history including **closed** PRs. If a draft PR is open, it reads both check-runs and commit statuses associated with that PR's exact **head SHA**. An unsuccessful, cancelled, timed-out or action-required check returns `HOLD_CHECKS_FAILED`. In-progress checks return `HOLD_CHECKS_PENDING`. Missing checks return `HOLD_NO_CHECK_EVIDENCE`, not an invented PASS. An unavailable checks/status API returns `HOLD_CHECKS_UNAVAILABLE`; evidence absence is not success.

Successful check results produce `REVIEW_READY_NO_AUTO_MERGE`. This means only that the currently reported checks have no failures; it **does not** certify code correctness, verify all possible tests, or approve merging.

If the FORMIC PR is closed without merge, the result is `HOLD_CLOSED_PR_RETRY_SUPPRESSED`. B161's PR-existence check was also updated to query all PR states, not just open PRs, so the same branch repair does not reappear after an unsuccessful closed PR. GitHub PR history is the persistent retry-suppression source of truth, even across workflow runs. There is no automatic reopened PR or force push.

## Evidence

Each scheduled B162 run uploads a JSON artifact with per-target PR state, check failures, pending checks and disposition. Each artifact is retained according to the workflow's configured retention period. It does **not** overwrite existing GitHub repository history and requires no observer quorum. Distinct run artifacts are historical records, although they are **not** permanent cryptographically signed attestations.

The local Git Pages B162 dashboard imports JSON artifacts, preserving no private credentials. No browser UI button pushes commits or triggers a workflow.

## Hard bounds

- No default-branch writes; no merges.
- No arbitrary patch generation or execution of code taken from discovered repos.
- No secret in artifact; only public repository metadata.
- No defined ISA: `:: isa` still unassigned.
- One observation layer deep, three source witnesses H/a1 O/b1 N/c1.
- The d view aggregates evidence and adds no new source register or ownership.
- Archived/private/foreign repositories are out of scope.

## Next bound

B163: policy-approved repair variants with fixed templates, reproducible checks, and stable per-repo failure backoff. Do not generalize automation until the real B161/B162 GitHub Actions jobs have been observed successfully.
