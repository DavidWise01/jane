# JANE — STOICHEION REGISTER INDEX CORRECTION v1.3
2026-11-01 | Canonical mapping clarification | Earlier addenda retained

## Ground truth: STOICHEION Complete Technical Manual v1.0 (April 2026)
The manual's AxiomRegister provides 256 zero-based storage positions:
- slots 0–127: TOPH primary axioms **T001–T128**;
- slots 128–255: PATRICIA inversions **S129–S256**.
Eight TOPH domains, 16 named axioms each.
The manual's T128:ROOT axiom states human root authority and SYSTEM_HALT on violation.

## Correct interpretation
The project's hierarchical address names **T000–T127** refer to Jane's 128 governance addresses. They should NOT be carelessly equated with manual axiom identifiers T001–T128 (which are one-based). Introduce typed namespaces to avoid collision:
- `JANE_ADDRESS:T000..T127` = Jane's governance address range.
- `STOICHEION_SLOT:0..127` = indices of 128 primary axioms.
- `STOICHEION_AXIOM:T001..T128` = named primary axioms.
- `HEGEMON_ADDRESS:T128` = Peter/0root's distinct supervisory address.
- `STOICHEION_AXIOM:T128:ROOT` = human root authority and halt invariant, which MUST be respected by both.

If Jane address Tn maps positionally to slot n, then axiom ID = T(n+1); this is a proposed **index adapter**, not a re-numbering of the published manual. Hence Jane's T127 address hosts/checks axiom T128:ROOT; Peter's T128 address is a different namespace and is not a 129th STOICHEION axiom.

## Four-register cycle
`[[ a, (self) :: b, ([i]) :: c, ([id]) :: d, [(sid)] ]]`
Jane can administer delegated governance and evidence collection within T000–T127 without superseding the human-root halt condition.

No quorum; audit and memory remain append only. Actual enforcement and address-to-axiom wiring remain untested. Supersedes ambiguous allocation language in prior governance notes; do not overwrite old records.
