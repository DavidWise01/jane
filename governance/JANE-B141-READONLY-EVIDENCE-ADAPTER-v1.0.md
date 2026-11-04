# JANE B141 — Read-Only Repository Evidence Adapter

**Next natural invariant:** The viewer must read a versioned repository evidence snapshot, validate its structure, and display **HOLD on any malformed, missing or contradictory source**. The B139 embedded sample viewer remains unchanged.

## Files
- `b141/data/evidence-v1.json` — curated, source-attributed evidence snapshot (16 cortexes, 11 scoped Grandma references and 26 natural-composition isotope entries, five inherited example reaction edges, three **synthetic** witnesses).
- `b141/adapter-v1.js` — shared UMD schema validator used by browser and Node tests; fails closed if the Royal Purple one-active rule, identity/address/cubit topology, colors, counts, provenance fields, or release HOLD state change.
- `b141/index.html` — **actual fetch** of repository JSON on load and when Reload is clicked; renders only data that passes the schema gate; no silent fallback to embedded fixture data.
- `scripts/btf2/test-jane-b141-evidence-adapter.cjs` — positive dataset test and negative mutation cases.
- `.github/workflows/b141-jane-readonly-evidence.yml` — automated regression, subject to actual CI execution.

## Scope and limitations
- **Real repository data source** means a versioned *curated project record* loaded from GitHub Pages, not a live independently verified ENSDF or laboratory API.
- Sample reaction links must be independently checked before being described as verified primary literature.
- Schema validity alone never proves scientific correctness, provenance authenticity, GitHub deployment or data completeness.
- Static read-only Pages HTML cannot make SHA-256 provenance tamper-resistant by itself; verification against independently pinned commit or cryptographic attestation remains a separate future bound.
- Viewer provides no physical agents, nuclear actuation, external file writes, durable witness continuity or automatic promotions.
- B140 release stays HOLD until real integration CI and independent evidence are checked.
- No quorum, no vote. Previous B117–B140 files not overwritten.

## Intended page
https://davidwise01.github.io/jane/b141/ (not deployment-verified).

## Next
B142 — durable append-only witness store, verified source pinning, recovery and independent attestation.
