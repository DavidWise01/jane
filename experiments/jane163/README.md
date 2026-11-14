# JANE 163 — The Witness to the Witness

**Natural invariant:** A signed scheduler history is not independently corroborated merely because a different key repeats it. Verify signed range commitments, compare heads, preserve conflicts and omissions, and trace actual custody ancestry.

## Scope and limits

The experiment authenticates Ed25519 checkpoint ranges and compares their contents against a locally available scheduler hash chain. Three *configured* administrator labels count as three claimed roots for the fixture, **not** proof that independently operated real-world organizations exist. The local SQLite evidence chain detects modification and most record-level discontinuity, but cannot demonstrate clean suffix truncation without a separately retained external head. The claimed `expected_end` is an injected benchmark; the protocol does not discover it on its own. The fixture does not persist consumed nonces between audit calls; it detects duplicate nonces within a single batch. This does not assert physical scheduler execution or scheduler-signed event origin; these receipts attest to range commitments only.

## Outcomes

- `MATCHED_FIXTURE_CUSTODY`: three configured distinct admin identities agree over a complete range.
- `INSUFFICIENT_DECLARED_CUSTODY`: too few declared distinct administrative roots.
- `SELECTIVE_SUPPRESSION`: an interior sequence is absent from all supplied ranges.
- `TRUNCATED_OR_MISSING_RANGE`: the observed ranges fail to cover the configured expected suffix.
- `CONFLICTING_COMMITMENTS`: roots claim inconsistent sequence-range heads or adjacency.
- `LOCAL_LOG_MISMATCH`: signed commitments disagree with a provided local hash-linked sequence.
- `INVALID_RECEIPTS`: invalid signatures, administrative identities or malformed claims detected.

## Run

```bash
python -m unittest -v test_witness.py
python witness.py
```

The frozen Jane parent stays unchanged, and all interpretations remain review-only.

## Next natural bound — JANE 164

Anchor checkpoint heads outside the observed process and challenge witnesses for compact consistency/inclusion proofs. A local append-only claim cannot detect valid prefix replays or clean suffix truncation without independent retention.
