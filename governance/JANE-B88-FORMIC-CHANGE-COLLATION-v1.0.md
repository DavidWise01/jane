# JANE B88 — FORMIC Change Collation / First Colony Work
2026-11-01 · executable bounded pipeline

Mission: one logical repository observer per BTF2 public pin; compare its latest metadata against the last successfully observed state for that same repository. Independently record missing/unknown observations. Jane's governing decisions do not require worker completion, votes, or consensus.

Pipeline:
1. BTF2 public repo discovery (no private listings).
2. B86 scoped read-only public metadata observations.
3. B87 append-only run snapshot (one immutable file per run, stable observer IDs).
4. B88 compare latest run with prior run, emit per-repository field changes and a hive summary. Treat API_UNAVAILABLE as UNKNOWN, not a repository deletion; a missing repo in a catalog scan is NOT evidence it was deleted.
5. Commit B87 run and B88 report in Jane only, not to observed repositories. Publish report through GitHub Pages at /b88/.

Tracked changes: archived, fork, updated_at, default_branch, pushed_at, open_issues_count, license_spdx, has_pages. Only compare values when status OBSERVED in both runs. Updated_at/open_issues_count are proxy metadata, not direct code review. Events have source run IDs and repo paths.

No LLM processes spawned, no autonomous third-party repo modifications. Collector workers are logical identities multiplexed through a bounded GitHub Actions job. This is real executable metadata collation, not a simulated dashboard if Actions succeeds.

Peter HEGEMON:T128 / 0root; Jane T000–T127; 128 STOICHEION axioms, not 128-worker cap. [[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]].
