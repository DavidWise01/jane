# B174 — Exact Before/After Tree Manifest

B174 creates a **data-only, deterministic manifest of the entire bounded source snapshot** before and after the exact fixed B161 bug-report template patch is applied in a disposable local worktree.

## Verification boundary

The evaluator accepts only a valid B168 proposal, B169 current-base observation, B170 local fixed-template check, B171 three-witness binding, B172 scratch Git pass, and B173 pinned complete tree. It rechecks every source Git blob and materializes the files with a strict 200-file / 2 MiB source cap. It inventories each actual local file by path, byte length, SHA-256, Git blob SHA-1, and executable-bit state. It then runs only Git's `apply --check` and `apply` commands; **no downloaded repository script is executed**.

After patch application, B174 inventories the worktree a second time and computes added, removed, modified, and preserved paths. The sole acceptable difference is one non-executable `.github/ISSUE_TEMPLATE/bug_report.md` with the exact canonical B161 content hash. The existing files must remain byte-for-byte identical, including executable status. The temporary working directory must be removed. The report contains an SHA-256 integrity digest of the complete manifest; modifying manifest contents without updating its digest is detected, but that hash is **not an identity or authorization signature**.

The only positive result is `EXACT_ONE_FILE_ADDITION`, never successful target CI. Any missing proof, snapshot, unwanted path change, compromised file digest, stale evidence, or failed cleanup results in HOLD. No source-target code executes, and no branch, PR, merge, retry or default-branch write is authorized.

## Autonomous operation

B174 scans at most eight actual committed B168 proof JSONs in `ecosystem/proposals/`. It re-observes fresh evidence and exports an immutable-per-run read-only artifact. No proof is `HOLD_NO_PROPOSALS`. Permissions are GitHub read-only.

Preserved form: `[a:122,b:122,c:122:d=a+b+c::isa]`. Three independent witnesses, one observer layer, derived d, no votes, no quorum, zero ISA instructions.

## B175 natural bound

Attest reproducibility: independently repeat the pinned before/after manifest and compare content hashes and the exact allowed change list without inventing CI or authority. Treat any mismatch as HOLD.
