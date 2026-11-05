# B175 — Repeated Deterministic Tree-Difference Proof

B175 is the natural reproducibility boundary following B174. The executor repeats **the same B174 on-disk evaluation twice**, each in its own disposable scratch working directory. It checks each complete before/after manifest with the B174 integrity auditor, then normalizes the contents and compares complete sorted file inventories and permitted changes.

Matching evidence includes repository name, original pinned base commit, source Git tree SHA, every original file path, byte length, Git blob SHA-1, content SHA-256 and executable-bit status; the after inventory and delta must also match. Each B174 run independently requires one exact addition of the B161 bug-report template and no other file modification or removal. If either evaluation fails or cleanup is not confirmed, B175 HOLDs. If two audited runs disagree, the outcome is `HOLD / NONDETERMINISTIC_MANIFEST`.

The positive state is `REPRODUCIBLE_TREE_DELTA_NO_EXECUTION`, not target repository CI success, identity authentication, or write consent. Repeating the same code does **not** constitute independent algorithmic implementations, voting, quorum, or three new witnesses. The a1/b1/c1 witnesses remain B168 proof, B169 base observation and B170 local patch evaluation; B175 is the derived read-only comparison.

The autonomous runner uses real, committed B168 proof files (maximum eight), re-observes the base, locally validates the fixed patch, binds the three witnesses within 300 seconds, performs the B172 scratch check, fetches a bounded B173 pinned Git tree, then repeats B174. No downloaded repository scripts execute. No PRs, branches, merges, retries or default-branch writes are authorized. No valid proof yields `HOLD_NO_PROPOSALS`.

B175 records a SHA-256 integrity attestation over normalized manifests and boundary flags. This detects unintended changes relative to the digest, but is not a signature attesting a human identity or owner authorization.

## Next natural bound — B176
Implement a *two-implementation differential audit*: compare independent tree inventory implementations using the same pinned source and permitted delta, without interpreting a match as proof of owner authorization or GitHub CI success.

Canonical `[a:122,b:122,c:122:d=a+b+c::isa]`: one observation layer, three independent source witnesses, zero defined ISA instructions, no quorum.
