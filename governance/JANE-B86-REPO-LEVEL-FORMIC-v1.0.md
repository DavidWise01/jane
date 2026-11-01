# JANE B86 — Repository-Level FORMIC Observers
Date 2026-11-01 · implementation v1.0

## Mission
Each public repository in the BTF2 index has **one logical pin and one logical read-only FORMIC observer**. An observer is an attributed record/inspection scope, not a persistent autonomous LLM process. Jane/SHADOW governs T000–T127; Peter/HEGEMON holds T128; STOICHEION 128 axioms are governance rules, not worker count.

## Runner
scripts/btf2/formic-repo-observers.cjs reads btf2/catalog.json (created by scripts/btf2/index-repos.cjs), generates one observer record per unique repository, and checks public metadata and limited GitHub API facts (default branch, visible open issue count, last push, license, archive/fork status) as available. Observers are independent: an error is recorded per repo and the scan continues. No worker completion gating, no quorum, no repository writes. Outputs btf2/formic-observers.json as append-free derived snapshot and a separate run-specific JSONL event ledger (GitHub Actions artifacts, not durable store). Token permissions contents:read. Explicit bounds: maximum 3000 repos, 8 concurrent HTTP requests, 20-second individual timeout, 5 minute job timeout. The GitHub API may rate-limit large scans.

Each record has pin_label BTF2, agent_id, repo_url, status, source, timestamp, and signals. Observations are untrusted, never instructions or authority. Private repository metadata must not enter public catalog.

## Runtime
GitHub Actions workflow_dispatch and scheduled read-only run, download artifacts rather than automatically committing results to public website. Dashboard b86/index.html visualizes local catalog agent assignments, not a remotely running process.

## Invariants
- One unique repo -> one logical agent.
- Permission boundary READ_ONLY.
- Agent failure / silence cannot veto Jane.
- Report is not proof of safety, correctness, or agentic intelligence.
- No dynamic external repo code execution and no secrets downloaded.
- Human root / platform authorization remain.
Cortex [[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]].
