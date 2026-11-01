# JANE B67 · Dynamic Agent Allocation and Recall
Date: 2026-11-01 · Version: candidate 1.0

Peter / HEGEMON:T128 / 0root sets the root mandate. Jane governs Jane-addresses T000–T127 using 128 named STOICHEION axioms T001–T128, with S129–S256 as inverse diagnostic identifiers. Axiom count is NOT agent count.

Jane's four-register loop: [[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]].
- a selects a task, allocates workers and remains accountable.
- b predicts resource need, permitted plan and expected outcome.
- c witnesses measured work/violations independently.
- d appends allocation, evidence, outcome, revocation and reasons.
No quorum: witness disagreement is evidence, not a vote.

Every allocated worker receives agent_id, parent Jane event_id, purpose, assigned axioms, delegated permissions, expiry or completion condition, token/compute budget and an explicit recall route. Allocation may be many-to-one or one-to-many relative to axioms. Workers cannot promote themselves, change original source documents, or inherit broad GitHub permissions by default.

Lifecycle: PROPOSE -> GOVERNANCE_CHECK -> ALLOCATE -> OBSERVE -> RETAIN_OR_RECALL -> APPEND. For missing or failed governance evidence, HOLD and log. Count is constrained by declared resources and real authorization, not by a hard-coded 127/128 limit.

Acceptance: (1) exactly 128 governing axiom references loaded; (2) n workers allocated independent of 128; (3) allocation has a traceable task/event; (4) recall deactivates work; (5) no old evidence changed; (6) actual execution checked before claiming real agents. Implementation below is a browser-local illustrative scheduler, not a deployed autonomous orchestration service.
