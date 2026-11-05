# B173 — Pinned Git Tree Snapshot, Data-Only Integration

The B173 natural boundary moves from B172's empty scratch repository to a **bounded materialization of the actual target repository's Git tree at the exact B168 base commit**. The materialized contents are treated only as data, and none of their scripts are executed.

After B168 proof, B169 live-base, B170 local fixed-template, B171 time-and-digest binding and B172 scratch apply pass, B173 reads repository metadata and its default branch ref, the pinned Git commit's tree SHA, the recursive tree listing and the contents of each Git blob. The verifier checks file sizes and Git blob-object hashes. It rechecks the branch ref after retrieval and holds on movement.

The data-only boundary refuses symlinks, submodules, unsupported file modes, unsafe paths, duplicate paths, trees with more than 200 entries, any file larger than 512 KiB or a total snapshot larger than 2 MiB. Large repositories HOLD rather than silently performing an incomplete snapshot. Each approved blob is written to a disposable local worktree. A fixed B161 issue-template diff is checked and applied there with Git, then the new file's exact bytes and SHA-256 are validated, the original source bytes rechecked, and the scratch tree removed. No file from the target repository is executed.

The positive result is `PINNED_TREE_PATCH_PASS`: the patch applies on a copied, verified source tree under the stated size limits. **It does not mean target-repository CI passed** or that repository-owner consent was authenticated. It never authorizes default-branch writes, branches, PRs, retries or merging.

The daily GitHub Actions job checks the implementation and scans up to eight existing committed proof envelopes under `ecosystem/proposals/`. No proof means `HOLD_NO_PROPOSALS`, never a fabricated successful evaluation. Run artifacts are retained up to 30 days as configured.

Preserve a1/H, b1/O and c1/N independent observations. d is read-only. No quorum, one observer layer, no defined ISA instructions.

## B174 natural boundary
Produce a **tree-level patch manifest and deterministic before/after diff audit**, including a complete audit that only the intended path changed. Preserve all bytes/paths as data and avoid executing repository scripts.
