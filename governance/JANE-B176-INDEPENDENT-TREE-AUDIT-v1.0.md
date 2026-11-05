# B176 — Independent Tree-Inventory Differential Audit

B175 proved that repeated B174 runs can produce identical manifests. B176 adds a **different inventory implementation** to detect algorithmic blind spots that two repeats of the same code might share.

A new iterative directory walker scans the actual temporary worktree during B174's **before** and **after** observation points. Unlike B174's recursive inventory, the new walker independently enumerates names, refuses symlinks, enforces file size and count bounds, computes SHA-256 content fingerprints, computes Git blob SHA-1 directly from the blob header and bytes, and reads executable-bit status. B174 does not supply the second implementation's file records; it supplies only the worktree paths and times to observe.

Each B174 source manifest must pass its existing audit and confirm workspace removal. B176 compares both independently obtained before and after inventories against the corresponding B174 records. It separately checks that precisely one new file was introduced—the canonical B161 bug-report template—and none of the source files changed or disappeared.

Agreement produces `DIFFERENTIAL_TREE_AGREEMENT_NO_EXECUTION`; disagreement, invalid proof, stale base, missing tree, suspicious symlink, unsupported path, incomplete workspace cleanup or unexpected authority produces HOLD. The attestation is an integrity digest, not a signature proving owner consent.

B176's independent inventory is algorithmically different but **observes the same underlying temporary filesystem**, not an independent GitHub source or third-party implementation. No source tree scripts execute, and the test cannot establish target-repository CI success.

The bounded autonomous runner consumes up to eight real committed B168 proofs from `ecosystem/proposals/`, reconstructs B169–B173 evidence, and invokes B176 on the exact pinned snapshot. No proofs mean `HOLD_NO_PROPOSALS`.

Three independent **source witnesses** remain a1/B168, b1/B169 and c1/B170. The derived B176 audit is not a new vote, quorum, or ISA instruction. It cannot create branches, PRs, retries, merges, or default-branch writes.

## B177 natural boundary

Perform a **semantic change audit** of the single allowed issue-template addition: validate its content without assuming every string or structured field is safe, while staying in a data-only, non-executing environment.
