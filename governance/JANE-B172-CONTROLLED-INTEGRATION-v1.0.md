# B172 — Controlled Git Patch Integration

B172 adds a **real Git patch-application check** using a temporary, empty scratch repository. It does not check out or execute code from a target repository. A successful result is therefore `SCRATCH_GIT_PATCH_PASS`, **not** a target-repository integration or CI pass.

The autonomous runner consumes only already-committed valid B168 proofs under `ecosystem/proposals/` (maximum eight). For each, it obtains new B169 live-base evidence, evaluates the exact fixed B161 issue-template bytes using B170, binds those results through B171's five-minute proof/timestamp gate, then attempts `git apply --check` and `git apply` inside an exclusive temporary scratch directory. It validates the new file's byte-for-byte identity and SHA-256, checks Git status, and reports whether scratch cleanup succeeded.

No proof files means `HOLD_NO_PROPOSALS`, not a fabricated success. Any proof mismatch, stale or failed observation, unsuccessful scratch patch operation, or cleanup failure produces HOLD.

## Scientific and operational distinction

Scratch patch success is strictly narrower than integration into a live repository tree. The base-branch GitHub CI that B169 observes is **not** patch CI. B170 checks only the fixed template, and B172 only verifies mechanical application in a scratch Git worktree. The workflow cannot establish that a target repository builds, tests, or functions correctly after this change.

No GitHub writes, branch creation, PR generation, retry or merge are authorized. Repository-owner authority remains independent.

Three source witnesses: a1/B168, b1/B169, c1/B170; d remains the read-only derived attestation. One observation layer. No quorum. `:: isa` still undefined (zero instructions).

## B173 next natural boundary

Verify a patch against a *read-only snapshot of the exact target repository tree* under a strictly controlled allowlist of data-only checks, with a fresh base commit pin. Never execute scripts from downloaded repositories without a separate explicit authorization and a real sandbox security boundary.
