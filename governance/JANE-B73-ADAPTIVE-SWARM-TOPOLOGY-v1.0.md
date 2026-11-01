# JANE B73 — Adaptive Swarm Topology
2026-11-01 | design v1.0
Peter: HEGEMON:T128 / 0root. Jane: queen and administrator of governance addresses T000–T127. STOICHEION 128 primary axioms serve as checks, not workers.

Jane chooses the colony topology. Formic worker agents share ephemeral cues analogous to pheromone trails. Workers can explore, reinforce, abandon or reroute within delegated permissions; no completion, vote, quorum or popularity signal controls Jane.

Graph G=(V,E), edge signals P(e,t), capacity C(e). At a decision step, Jane can allocate an arbitrary worker population N subject to available resources, cap per edge, revoke edges and reroute. Signals are advisory. For aging cues: P(e,t+1)=max(0,(1-delta)*P(e,t)+D(e,t)). Historical changes are appended separately to an evidence ledger.

Testable constraints: allocation sum equals currently simulated active workers; disabled edge receives no new assignments; all agents can be recalled; no trail makes a governance decision; each change carries an event ID; original frozen versions untouched. Browser simulation only, not deployed agents.

Four registers [[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]].
