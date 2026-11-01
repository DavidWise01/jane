# JANE B68 — Agent Specialization & Homeostatic Allocation
Date: 2026-11-01 · Candidate 1.0

## Authority
HEGEMON:T128 = Peter / 0root. JANE administers addresses T000–T127, adapted to STOICHEION primary axioms T001–T128 with inverse diagnostics S129–S256. These are governance checks, not 128 workers. Agents are dynamically allocated and counted separately.

## Role model
Observe (read authorized public data), Verify (compare provenance and claims), Remember (append evidence), Audit (evaluate rule compliance), and Coordinate (monitor assignment state). Distinct capabilities and scopes apply. Agents can share axioms; one axiom can apply to multiple agents.

## Homeostatic controller
Given nonnegative queued jobs q_r by role, service rate k_r jobs per worker per cycle, and bounded cap C:
target_r = ceil(q_r / k_r)
Budget reservation: min(target, C) by weighted priority and deterministic tie-break.
Use hysteresis to avoid churn: scale out immediately if backlog rises; scale in only after two consecutive low-demand evaluations, recall idle workers first.
No fabricated work completion: simulation load is an explicit user-provided queue. No web crawler or agent service is running.
The desired number of agents is not constrained by 128, although the sandbox implementation imposes a configurable demo cap.

## Four-register cycle
a(self): issue role assignments and recalls within authorized scope.
b([i]): predict target capacity and service.
c([id]): observe incoming queue and allocated capacity, measure errors.
d[(sid)]: append decisions, reasons and discrepancies in an immutable-in-session event list.

No quorum. Root/human halt remains effective, and privilege elevation is prohibited. External writes require separate authorization.

## Acceptance
(1) 128 mapped rules preserved; (2) changing workloads changes role allocation; (3) idle capacity recalled after hysteresis; (4) capacity never exceeds demo budget; (5) recall leaves a trace; (6) uncertainty and missing execution evidence remain labeled.
Status: browser-local interactive allocation simulator; no deployed autonomous workers or durable backend.
