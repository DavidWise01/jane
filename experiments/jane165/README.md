# JANE 165 — The Stale Witness

**Natural invariant:** Authenticated history is not necessarily current history.

The source `freshness.py` checks Ed25519-signed custodian checkpoint envelopes carrying a sequence, head, nonce and integer observation timestamp. The configured freshness policy defaults to 300 seconds maximum age, 30 seconds allowed future skew, and 3 distinct declared administrative roots. It classifies stale-but-valid signatures as `STALE_HISTORY` and restricts their use to historical continuity. It persistently detects nonce replay, checkpoint rollback, and same-sequence signed forks using a separate SQLite record store.

The evaluator distinguishes `FRESH_FIXTURE_QUORUM_NO_COMPLETENESS_PROOF`, `AUTHENTIC_HISTORIC_ONLY`, `LOCAL_HEAD_MISMATCH`, `CONFLICTING_CHECKPOINTS`, and `INSUFFICIENT_FRESH_CUSTODY`. The local append-only audit hash chain requires an externally held head to guard against clean truncation.

Run: `python -m unittest -q test_freshness.py` (46 tests). Run `python freshness.py` for the fixture evidence packet. The deterministic fixture timestamps are controlled test inputs, not independently time-synchronized observations. `now` must be supplied from a trusted source in operational use. Three fixture keys and named administrators do not establish independent operators, no external host was contacted, and a fresh record does not establish globally complete history.

Jane remains frozen; no automatically authorized learning or active intervention occurs.

## Next natural bound — JANE 166: Conflicting Clocks

If witnesses report different valid-looking times, FLAY must reconcile bounded clock uncertainty, identify impossible time ordering, and avoid claiming current completeness from inconsistent Chronos sources.