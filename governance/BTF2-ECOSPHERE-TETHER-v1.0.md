# BTF2 — Back to the Future 2 · GitHub Ecosphere Tether
2026-11-01 | v1.0

One visual pin per **public** repository owned by DavidWise01. Every pin links to the actual GitHub repository. If a repository has a declared homepage link, show that as unverified; the existence of a GitHub Pages website is not inferred from the repository name.

The BTF2 dashboard is in DavidWise01/jane/btf2/index.html. GitHub Actions retrieves all public owner repositories with paginated GitHub REST API and writes an append/update snapshot to btf2/catalog.json. The action makes a single authorized write to its own repository; it does not edit other repositories. Repo metadata includes name, URL, description, homepage, updated_at, archived and fork flags. All remote text is treated as untrusted and inserted with textContent.

Each repository is represented by one pin in a deterministic planar orbital layout. Pins are clickable, searchable, and filtered by fork/archive state. Snapshot source, timestamp, and count disclosed. If the snapshot does not exist, browser API fallback attempts discovery but GitHub unauthenticated rate limits can prevent a full count.

Security: never publish private repo metadata in a public website. The remote indexer uses /users/DavidWise01/repos (public only), not /user/repos. Site is a **link hub**, not code execution or autonomous repo access. The BTF2 mission pin is infrastructure for the HEGEMON internet timing research; no claims about actual relativistic dilation.

No subagent completion gate; no quorum. Peter HEGEMON:T128, Jane T000–T127, cortex [[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]].
