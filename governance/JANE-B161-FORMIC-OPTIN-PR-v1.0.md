# B161 — FORMIC opt-in agent for the DavidWise01 GitHub ecosphere

This follows B160's scheduled public repository observation pipeline. It gives each participating repository a **local, explicit policy gate** for a narrowly scoped, optional code hygiene proposal.

## Run-time decisions

1. The B161 workflow runs on a daily GitHub Actions schedule and via `workflow_dispatch`. It runs a deterministic Node regression suite before accessing remote repositories.
2. A bounded scout discovers public repositories owned by `DavidWise01`; archived, disabled, forked, private, or out-of-scope targets HOLD.
3. It reads `.formic/policy.json` from the repository default branch. Missing or malformed policy HOLD. The policy requires `schema=FORMIC-REPO-POLICY-v1`, `enabled=true`, `allowed_repairs` containing `BUG_REPORT_TEMPLATE`, and `max_open_pull_requests=1`.
4. If `.github/ISSUE_TEMPLATE/bug_report.md` already exists, the agent does nothing. If an equivalent FORMIC PR or branch already exists, the agent does nothing.
5. If the workflow environment explicitly enables PR creation and `FORMIC_REPO_TOKEN` exists, it creates a new branch `formic/b161-bug-report`, adds a basic reproducible bug report template, and opens a **draft PR**. It does not merge, force-push, delete files, or modify default branches.
6. On API failure it records HOLD; reports are uploaded to the Jane workflow artifact. The workflow targets at most 3 opted-in public repositories per run. The agent does not run code copied from discovered repositories.

## Operational preconditions

Scheduled GitHub Actions only execute when enabled and GitHub accepts the workflow. Without the opt-in policy and write-enabled credentials, B161 runs in dry-run mode, so do not claim it has opened PRs. To enable PRs, the `jane` repository needs a dedicated **fine-grained secret** `FORMIC_REPO_TOKEN` with explicit access only to target repositories (Contents and Pull requests write scopes), plus an Actions variable `FORMIC_ENABLE_PR_CREATION=true`. The workflow's own `GITHUB_TOKEN` is read-only. Granting broad organization-owner administrator tokens is discouraged.

The owner sets policy independently in each repository. No public-policy file authorizes access to private repositories. Note that a repository-level policy is not a security boundary against malicious contributors with push access to its default branch; combine it with branch protection and tightly scoped credentials.

B161 is an autonomous *planning and draft-proposal* agent, not an unrestricted self-modifying swarm. No cross-repository direct writes on default branches, no automated merge, no hidden authority transfer.

## Symbolic kernel preservation

```
[a:122,b:122,c:122 : d=a+b+c :: isa]
H/a1: inventory evidence     O/b1: health signals
N/c1: repair proposal        d: read-only aggregate
```

Three independent witnesses at one observation layer, no vote/quorum. `:: isa` remains undefined: zero instructions. 366 cells remain a symbolic register scheme, **not** a count of actual GitHub repositories. No empirical atomic physics promotion.

## Next bound

B162: read-only cross-repository policy discovery at scale, automated PR verification, owner-specific suppression lists, and a failure-preserving repair outcome ledger. Do not permit direct branch edits or merge actions without independent safeguards.
