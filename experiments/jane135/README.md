# JANE 135 — Persistent Trust Across Generations

Canonical Chronos: `{{ - year:month:day || hour:minute:second || degree.arcminute.arcsecond || }}`

A signed key-rotation event binds a new Ed25519 key to the **same custody root**. SQLite stores nonces by custody, not key, so a replay cannot succeed merely by rotating the key. The event log uses hash chaining. A separately retained external head is necessary to catch clean log truncation.

**Verified local experiment:** 20/20 tests passed on the full offline implementation. This repository version is a compact implementation with an eight-test reproduction, not identical to the full tested files. Run `python -m unittest discover -s experiments/jane135 -p 'test_*.py' -v` after installing `cryptography`.

## Limitations
The genesis key registry and custody identity are locally supplied fixtures; actual third-party witness independence and external anchoring have not been deployed. Chronos is recorded as a signed string but clock accuracy is not authenticated. Persistence uses SQLite and is not tamper-resistant against administrators. SQLite hash-chain truncation needs an external trusted head. No autonomous learning takes place; Jane's decision remains undecided.

## Next natural evolution: JANE 136
Independently publish checkpoint heads to multiple administratively separate custodians, verify signed receipts and append-only continuity, and test malicious rollback of an otherwise valid local database.
