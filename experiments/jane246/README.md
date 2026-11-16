# JANE 246 — The Three Clocks That Shared One Authority

**Invariant:** `Three Signed Clocks != Three Independent Time Authorities`.

A supplied graph records `clock → timeserver → authority / operator / credential / platform` relationships. The verifier collapses connected overlapping dependency paths rather than counting clock signatures or hostnames.

**Local reproducibility:** 34 Python regression tests passed. The synthetic fixture has three clocks and one shared upstream authority: `SHARED_TIME_AUTHORITY_ANCESTRY`, one dependency cluster. An alternate fixture with separate declared authorities returns `DISTINCT_DECLARED_AUTHORITY_ANCESTRY_ONLY`.

**Boundary:** This is a claimed ancestry graph, not authenticated upstream time synchronization. Neither successful fixture proves independent clocks or truthful UTC. No running A.C.I. chose a task and no action was authorized.

Local complete ZIP: JANE 246 package delivered in conversation. It contains `time_ancestry.py`, `test_time_ancestry.py`, fixtures, receipts, an offline HTML chapter, and a manual workflow file. Those local Python files must be published before enabling the workflow.

Next: JANE 247 — The Authority That Copied Its Upstream Clock.
