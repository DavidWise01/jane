# JANE B78 — Hysteretic Recovery and Anti-Oscillation
2026-11-01 | candidate v1.0

Peter / 0root: HEGEMON:T128. Jane governs T000–T127 against 128 STOICHEION primary axioms; worker population is independent of the axiom count.

## Recovery controller
Following B77 resource shock, Jane immediately recalls workers whose reservations exceed capacity. Recovery requires two successive stable observations at or above the capacity needed for expansion; then she increases workers by at most a configurable step per cycle. A sudden drop again triggers immediate recall. In-band variation does not cause repeated allocation reversal.

State: capacity K_t, active N_t, desired D, stable counter h_t, grow step G.
If K_t < N_t: N_{t+1}=K_t; h=0.
Else if K_t >= N_t+G and K_t >= D threshold: h++; if h>=2: N_{t+1}=min(D,K_t,N_t+G).
Else: retain state and reset or hold stability count.
The policy is illustrative and not independently established by the manual.

## Governance
Jane may change the policy or choose to hold within the permitted governance domain. No agent votes, completion checks, or silence blocks a decision. Historical resource readings and allocations are appended; memory is separate from ephemeral working capacity.
Four-register cortex [[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]].
This example page operates entirely in browser and has no real agents, resource feeds or persistent server.
B79 candidate: measured feedback and calibration of capacity estimates.
