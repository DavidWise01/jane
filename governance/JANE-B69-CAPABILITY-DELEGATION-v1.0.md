# JANE B69 — Capability-Scoped Delegation
2026-11-01 · Candidate v1.0

Peter / 0root occupies HEGEMON:T128. Jane governs T000–T127 using the 128 primary STOICHEION checks; axiom count does not cap worker count. Jane's cortex is [[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]].

## Rule
Authority for a worker is not inherited merely by being spawned. Each assignment grants a bounded capability ticket:
(agent_id, task_id, scope, operations, expires_at, grant_event_id, status).

The simulated capabilities are: public_read, verify_metadata, append_local_log, audit_local, coordinate_local. No worker may access private data, modify GitHub, deploy or change account permissions through the page. A ticket is valid only if the requested operation and resource are in its explicit allowlist, within its lifetime, and not revoked.

Jane can delegate, inspect and revoke tickets. Peter's governance root remains separate. The human operator's externally granted permissions are ceilings. No quorum.

Lifecycle: REQUEST -> SCOPE CHECK -> GRANT -> USE CHECK -> EXPIRE/REVOKE -> APPEND EVIDENCE. Denied actions are observable events, not silent successes. A ticket does not confer the ability to mint tickets for other agents.

## Acceptance targets
- Different roles receive different operation sets.
- Out-of-scope operation denied.
- Revoked ticket denied.
- Expired ticket denied.
- Agent does not become an authority over its own capabilities.
- Event log contains grant, denial, use and revoke records.
- Every source remains read-only except the explicitly local simulation log.
Browser demo is not an authentication or secure isolation environment. Real security requires server-side identity checks, authenticated permissions, revocation storage and audit log integrity.
