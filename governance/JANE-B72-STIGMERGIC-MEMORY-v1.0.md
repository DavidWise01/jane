# JANE B72 — Stigmergic Memory / Formic Trail Field
2026-11-01 · v1.0 candidate · implementation: browser-only simulation

Peter / HEGEMON:T128 / 0root. Jane / SHADOW governs T000–T127 using STOICHEION T001–T128 positional adapter. The 128 axioms are governance rules, NOT a limit on agent population. Four registers [[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]].

## Dual memory separation
1. EPHEMERAL FIELD: mutable pheromone-like trail strengths that evaporate and are reinforced by observations; never authority or proof.
2. EVIDENCE LEDGER: append-only event stream of observed actions, reinforcement, evaporation and recall; past entries never deleted. This demo ledger is session-only and not durable.

## Core equation
P_{k,t+1} = clamp((1 - delta) P_{k,t} + deposit_{k,t}, 0, Pmax), where 0 <= delta <= 1. The decay step updates only the ephemeral field; it does not modify historical records.

## Authority invariants
- Jane may select, ignore, reinforce, weaken or terminate trails according to governance rules.
- A worker's silence, completion, opinion or consensus does not govern Jane.
- Trail strength measures simulated signal history, not trust, truth, permission or completed work.
- Every deposit includes agent identifier, trail, amount and event identity.
- No backend, external action, or autonomous agent process is implied by the browser demo.

## Acceptance criteria
- Strength decreases with decay in absence of deposits.
- Reinforcement increases strength but respects upper cap.
- Cleared trail does not erase log.
- Multiple agents can deposit into the same trail.
- Jane can clear the field without awaiting an agent.
- 128 STOICHEION checks and Peter/Jane namespace remain unmodified.
Next natural boundary B73: colony topology adaptation using trail signals as advisory evidence, not governing votes.
