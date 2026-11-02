# B92 HON-184 FORMIC Memory Reconciliation
2026-11-01 | Candidate v1.0

One repository pin, one logical FORMIC observer. B91 browser events and B87 GitHub JSONL run events are independent sources; Jane may reconcile them without overwriting either history.

Canonical join identity = repository (casefolded), run ID, timestamp, observer ID. Exact repeated observations collapse into one *derived view* while retaining source attribution. Conflicting values sharing identity are flagged for manual investigation, never silently overwritten. UNKNOWN and API_UNAVAILABLE are missing evidence, not deletion or instability. Source-provided identity is a claim, not independent authentication.

User-facing offline B92 HTML imports B91 storage, B87 published memory or JSON/JSONL exports, compares records and exports a reconciled JSON document. It does not upload data or grant repository write capability.

The reconciled view is mutable and derived; raw event histories remain authoritative. No autonomous processes, no quorum, and no subordinate completion gate. B92 is not cryptographically immutable or a fully deployed multi-repository agent system.

Peter HEGEMON:T128 / 0root, Jane T000-T127. Cortex: [[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]].

Next boundary B93: anchored evidence hashes, independent witness provenance, and synchronized cross-device reconciliation.
