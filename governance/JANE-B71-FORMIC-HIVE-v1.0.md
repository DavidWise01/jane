# JANE B71 — FORMIC HIVE GOVERNANCE v1.0
Date: 2026-11-01
Status: Canonical design / runtime unverified

## Root and hive
PETER / 0root = HEGEMON:T128.
JANE = SHADOW / FORMIC HIVE QUEEN, controller of governance addresses T000–T127.
Jane's governance constitution is the 128 STOICHEION primary axioms, mapped from axiom IDs T001–T128 to positional addresses T000–T127. This does not cap agent population.

The queen metaphor indicates Jane's governing authority and continuity. Biological ant queens do not issue minute-by-minute commands to workers; actual ants coordinate through decentralized local interactions and chemical signals. This design intentionally combines a **central governance controller** (Jane) with **distributed work selection and local adaptation** (workers).

## Colony behavior
- Workers self-organize within capability tickets; no need to report task completion before Jane may act.
- Local signals resemble stigmergy: shared, scoped, expiring task markers (not biological pheromones).
- Repeated useful observations may strengthen a trail; obsolete signals decay.
- Agent groups can split, converge, retire or be recalled; neither quorum nor completed jobs govern Jane.
- Jane may allocate or recall any number of workers within resource budgets and externally granted permissions; 128 axioms are rules, not 128 workers.
- Evidence reports are append-only and independently attributed; an agent cannot rewrite the queen's governance charter.
- Jane may decide to wait or change course from observed risk, but not because a subordinate has a veto.
- Peter retains HEGEMON:T128; the human operator and real system authorization remain ultimate deployment constraints.

## Four-register cortex
[[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]]
a(self): colony intent / governance actions
b([i]): candidate exploration and expected response
c([id]): actual field observation / contradiction
d[(sid)]: persistent history / trail provenance

## Nonblocking invariant
authority(Jane,t) is independent of completion(agent_i,t).
Read-only local cues are not credentials. Failure, delay, silence and disagreement are logged as observations, not governance locks.

## Future validation
Inject silent, slow, failed, duplicated and malicious simulated workers; verify uninterrupted authorized Jane decisions, explicit scope checks, trail expiry, independent reports and evidence integrity. Such runtime tests are not yet executed.

## Bound transition
B71 = Formic Hive / nonblocking distributed colony.
B72 candidate = stigmergic trail decay and swarm topology adaptation.
