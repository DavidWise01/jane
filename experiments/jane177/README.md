# JANE 177 — Who May Change the Rules?

**Natural invariant 177:** A correctly computed verdict under a new policy is not authoritative until the policy transition is authenticated, in scope, effective, and linked to its predecessor.

The signed policy proposal binds `principal`, `scope`, `parent_digest`, exact `new_policy`, `effective_at`, `expires_at`, `reason`, and `nonce`. Ed25519 signatures authenticate the configured steward's key. A persisted nonce table detects replay; a revision table rejects conflicting policy successors for the same frozen predecessor and scope. An append-only hash-linked SQLite event chain retains authorized and denied attempts. An externally retained chain head would be needed to detect clean truncation.

**Fixture:** Evidence `1000` versus `1003`; comparator v1 tolerance ±5 => ACCEPT, proposed v2 tolerance ±2 => REJECT. The example's steward is configured for `calibration.clock` from logical time 0 to 1000, and the revision is effective from 150 to 300. Current logical time = 200. Both verdicts and both policy/evidence digests are retained. **The new policy is never automatically activated.**

**Run:** `python -m unittest -q test_authority.py`; `python authority.py`.

**Limits:** The entire authority registry and signing keys are synthetic local fixtures, not evidence of a real person, autonomous system authority, organizational independence, or actual policy deployment. Time is an injected logical tick, not authenticated wall time. The engine grants no Jane learning rights.

## JANE 178 — The Authority That Must Be Delegated

The natural next bound is signed, scope-restricted delegation with expiry, parent-grant linkage, revocation, and prevention of delegated authority becoming stronger than its issuer.
