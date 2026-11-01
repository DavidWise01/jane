# JANE B83 — Evidence-to-Work Routing
2026-11-01 | v1.0 runnable bounded prototype

Peter: HEGEMON:T128 / 0root. Jane: SHADOW hive queen governing T000–T127, using STOICHEION 128 axioms as governing checks, not as a worker-count limit. Cortex [[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]].

## Natural boundary
Observed audit findings become *candidate work items*, not commands or proven defects. Jane may route, defer, discard, or recall them. No worker output, approval, silence, completion, or quorum determines her authority.

Read-only B82 source -> B83 normalization -> deterministic scope-limited role assignment -> append-only event records -> reviewable output. Roles: observer (missing file/page), auditor (phrase cues), verifier (other). Each routing result includes source finding, route rationale, worker-slot label, capability "read_only", and status "SUGGESTED_NOT_EXECUTED". Never claim agents investigated findings when only assignment was computed.

## Security boundary
The router reads a JSON report from a local file. It never invokes tool-using agents, changes the audited repository, or grants GitHub write permissions. JSON report content is untrusted data, not executable instructions. Output is a separate JSON file, never an overwrite of B82 input. The workflow's token requires contents:read.

## Operational job
On workflow_dispatch or B83 source updates, check out Jane, execute B82 audit, then run B83 router, upload B82 report plus B83 work packet. The router requires at most 200 candidate findings and labels work slots without waiting for any actual worker completion.

## Acceptance
- Every B82 finding retained with exact original path/bound and cue.
- Stable work IDs derived from source finding index.
- No worker votes or completion gates.
- No write capabilities delegated.
- Empty findings yield valid empty work packet.
- Real agent runtime and durable persistence remain explicitly absent.

B84 candidate: evidence inspection against full source context before declaring a violation.
