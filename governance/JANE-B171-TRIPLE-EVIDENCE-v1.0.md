# B171 — Triple Evidence Binding

B171 combines **three independently described observations** without voting, quorum, new witnesses, or implicit authority:
- **a1 / B168:** exact proposed diff, audited against a deterministic one-file fixed template, and the SHA-256 of its full proposal envelope;
- **b1 / B169:** real read-only observation of current public repository metadata, unchanged default-branch SHA, target absence and existing-base CI evidence. This must carry the **same B168 digest**;
- **c1 / B170:** disposable local evaluation of the exact B168 patch bytes, seven local validation checks and successful cleanup. This also must carry the same digest.

The derived **d** attestation requires the same source repository, the same base SHA, unmodified evidence digests and no more than 300 seconds between the start of remote observation, local evaluation, and assembly. Future, stale, missing, conflicting, unsuccessful or mismatched evidence returns `HOLD`. The positive state is `EVIDENCE_BOUND_NO_EXECUTION`.

**B169 success does not mean proposed patch CI passed.** It observes the **original base commit's existing CI**, while B170 performs seven local fixed-template checks. B171 never treats those as the same test or authorizes installation. The B168 expected check names remain requirements for a future integration evaluation, not evidence of execution.

B171 reads at most eight real, committed proof JSONs under `ecosystem/proposals`, never invents a proof, and records `HOLD_NO_PROPOSALS` otherwise. The new GitHub Actions workflow runs native tests, processes any existing proposals, and uploads a per-run artifact. No repository writes or PRs are made.

The resulting SHA-256 attestation digest detects alteration relative to the reported digest, but does not independently prove human authorization, GitHub identity, or permanent provenance. It is not a cryptographic signature.

Original invariant: `[a:122,b:122,c:122:d=a+b+c::isa]`. Three source witnesses, single observation layer, zero ISA instructions, no quorum.

## B172 next natural bound

Verify B171's signed-or-attributed source evidence against actual test runs for a proposed patch in a controlled non-executable integration environment before any authorized draft-PR stage. Keep owner authorization distinct from a green check.
