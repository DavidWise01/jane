# B168 — Proof-Carrying Repair Proposal

B167 established only independent **authorization evidence**, not permission to act. B168 can prepare an exact, deterministic one-file change proposal for the existing B161 bug-report template **without creating a branch or pull request**.

Every candidate is restricted to a public, non-archived `DavidWise01` repository whose `.formic/policy.json` explicitly opts into `BUG_REPORT_TEMPLATE`. A supplied B167 record must have `POLICY_EVIDENCE_PRESENT` while `mayCreatePR`, `mayRetry` and `mayMerge` are all false. The target file must be absent, and the base branch commit must be identified by a 40-character SHA.

The proof envelope contains:
- exact repository identity, default branch and pinned base SHA;
- one `ADD_FILE` operation to `.github/ISSUE_TEMPLATE/bug_report.md`;
- full deterministic content, its SHA-256 and a textual unified diff;
- a list of required checks that are marked **expected, not observed or passed**;
- policy evidence designation and explicit absence of write/merge/retry authority;
- SHA-256 over the complete envelope.

Tampering with the content, diff, digest or grant flags fails the verifier. Repeated repositories cannot be added to a single proof registry.

## What this boundary does not do

It does not execute any target code, fetch GitHub secrets, create branches, open PRs, rerun old repairs, authorize merges or grant default-branch write authority. It does not treat `POLICY_EVIDENCE_PRESENT` as permission. The deterministic proof is an inspectable candidate; a later stage may compare it to a fresh, separately authorized target repository state.

One observation layer, three independent witnesses (a1, b1, c1), d a derived read-only view, zero ISA instructions, no quorum.

## Next natural bound
B169 should compare the proposal against the **fresh remote base and actual check results**, detecting drift before any possible future owner-reviewed draft PR action. No implicit execution authority.
