# B165 — Owner intent evidence, no implicit retry

Cooldown expiry is never authorization. A versioned `FORMIC-RETRY-INTENT-v1` declaration must identify its repository, previous PR number, previous PR head SHA, reason, expiry, and an explicit allow_retry flag. The read-only verifier also requires supporting GitHub default-branch commit attribution evidence and exact policy digest. Missing evidence returns HOLD.

GitHub commit signature verification and account attribution do not independently authenticate the human owner. Even with all evidence present, B165 grants no write or merge authority. B161's more conservative closed-PR suppression remains in force.

The source implementation and regression tests are fixture-based and read-only; live owner-attestation retrieval has not yet been implemented. SHA256 evidence chains detect changes relative to a recorded head, but do not establish authorship.

Three original source witnesses a1/b1/c1; one observation layer; d derived view; no quorum; zero ISA instructions.
