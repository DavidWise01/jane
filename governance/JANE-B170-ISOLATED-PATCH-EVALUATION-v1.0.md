# B170 — Isolated Local Patch Evaluation

**Boundary:** a proposed patch may be inspected and validated without granting any ability to install it. B170 accepts a valid proof-carrying B168 envelope for one exact `ADD_FILE` change: the canonical B161 GitHub bug-report issue template.

The evaluation runs inside a disposable temporary directory. It writes the proposed content using an exclusive-create flag, reads it back, and executes **seven fixed local checks**: exact bytes, SHA-256, canonical template identity, YAML front matter delimiters, reproduction instructions, expected-versus-actual sections, and warning to remove secrets. It then deletes its temporary workspace and records whether cleanup succeeded. Malformed, modified, non-template or duplicate-file proposals HOLD.

This is a real evaluation of the **fixed template**, not execution of a target repository build. Temporary filesystem isolation alone is not a security sandbox for arbitrary untrusted code; B170 does not execute such code at all.

The scanner reads at most eight existing, committed proof JSON files under `ecosystem/proposals/`, with no inference or synthesis of authority. Missing proposals produce `HOLD_NO_PROPOSALS`. The workflow runs tests, executes local validation, and uploads the resulting per-run artifact. It needs read-only repository permissions and no cross-repository write tokens.

The statuses `LOCAL_CHECKS_PASS` and `githubCiObserved=false` must coexist. A B170 PASS does not establish that a patch works with the target repo, cannot override a B169 drift HOLD, and never authorizes branch creation, draft PRs, retries, merges or default-branch writes.

Preserve a1/b1/c1 as three independent witnesses, one observation layer, d as derived view, no quorum and `:: isa` undefined with zero instructions.

## B171
Bind B168 proof, B169 fresh-base evidence and B170 local-check report in one time-limited comparison, preserving individual witnesses and requiring the exact same proposal SHA before any future action stage.
