# JANE B87 — Per-Repository FORMIC Memory
Date 2026-11-01 · v1.0

Peter: HEGEMON:T128/0root. Jane: SHADOW governing T000–T127. Four-register cortex [[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]].

## Bound
One BTF2 public repository pin → one logical FORMIC observer → append-only attributable memory. Every snapshot is evidence, not authority. No subordinate votes, completion dependency, or quorum.

## Memory model
At each successfully completed scan, write immutable run file btf2/memory/runs/<run-id>.jsonl. Each line has schema, run id, recorded time, pin BTF2, repository, observer ID (stable derivation from repository name), status, source and raw metadata fields. Prior run paths remain unchanged. Write or update btf2/memory/index.json as a *derived pointer* (not the authoritative ledger); preserve older run files. Jane's cortex reads history and presents evidence, not task approvals.
Event identity is run_id + repository identity. A stable observer identifier must NOT depend on pagination order.
Repositories omitted from an incomplete scan are not marked deleted. API failures preserve UNKNOWN.
Public-repository metadata only; do not include private repos or secrets.

## Runtime
B87 GitHub Action performs BTF2 discovery, B86 scoped metadata observation, then B87 memory append, commits a new run file and refreshes the derived index. Requires write rights ONLY to this Jane repository. GitHub Actions history is the stronger immutable version record; regular Git branch files can be rewritten by administrators and are not cryptographic append-only storage. A tamper-evident anchored ledger would require a subsequent bound.
No persistent LLM worker is instantiated.

## Acceptance
No old run file overwritten; stable worker IDs per repository; duplicate run ID errors; each result preserves status and provenance; failures and unknowns represented explicitly. Historical snapshots support comparing successive observations.
Next bound B88: change detection, causal provenance and independent witnesses.
