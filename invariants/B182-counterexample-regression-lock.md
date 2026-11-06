# B182 — Counterexample Regression Lock

State: SPECIFICATION CANONICAL; standalone Node.js implementation and 15 local B181+B182 tests pass. Live B180 parser integration is not claimed.

## Invariant
Each verified B181 disagreement becomes an append-only regression witness with its immutable original input, minimized input, SHA-256 digests, exact left/right acceptance and error category signature, source, timestamp, unique case ID, previous entry hash, and entry hash.

Replay never rewrites a witness. It returns exactly one of:
- REPRODUCED: original mismatch signature reproduced exactly.
- CHANGED_MISMATCH: parsers still disagree but the signature differs.
- NO_LONGER_REPRODUCES: mismatch disappeared.
- EVALUATION_ERROR: evaluator threw.
- CORRUPT: witness integrity failed.

Only NO_LONGER_REPRODUCES permits a separately recorded explicit resolution event with reason, actor, timestamp, and witness hash. A changed mismatch is not silently considered a fix.

## Bounds
- 12 cases maximum per fixture ledger
- 16,384 bytes maximum original input
- Exact content and digest checks
- Unique stable case IDs
- Hash-linked append-only records
- No quorum, no silent replacement, no inferred resolution
- B181 minimization maintains 256 evaluation attempts and 32 passes maximum.

## Test record
2026-11-05: 15/15 Node.js tests passed (7 B181 + 8 B182) using an illustrative synthetic pair of parser evaluators. This is not a test of B180's live parser implementation.

## Next boundary
B183: Regression Replay Provenance — bind each replay to parser identity/version, environment, and executable digest. Compare only compatible observations.
