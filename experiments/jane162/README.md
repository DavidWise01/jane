# JANE 162 — The Observer Who Can Lie

**Invariant:** `VALID_LOG != TRUTHFUL_OBSERVATION`.

A scheduler signs every decision with Ed25519. Each receipt contains its scheduler identity, epoch, monotonic sequence, tick, enabled-agent set, selected agent, and the digest of the previous signed receipt. FLAY verifies the configured signing key and compares untrusted observer reports to those signed receipts. SQLite preserves receipts and a local hash-linked append-only audit of acceptance, rejections and reconciliations.

The verifier exposes `MISSING_SEQUENCE`, `BROKEN_SIGNED_CHAIN`, `BAD_SIGNATURE`, `REPLAY`, `SIGNED_EQUIVOCATION`, `OBSERVER_CONTRADICTION`, `OBSERVER_OMISSION`, and `MISSING_SIGNED_SOURCE`. A forged or missing observer report never rewrites the original accepted signed receipt.

## Reproduce

```sh
python -m unittest -v test_provenance.py
python provenance.py
```

## Explicit trust limitations

- Configured signing keys are fixture credentials; signatures verify possession of signing keys, **not actual scheduler hardware execution**.
- A signed scheduler can still lie; an observer can also suppress the entire receipt stream.
- Without a separately retained and authenticated external head, the local hash ledger cannot detect clean truncation, database replacement, or suppression of final events.
- Missing source events cannot be proven from an unanchored stream of receipts alone; expected source windows must come from independently established commitments.
- The bounded-fairness analysis of JANE 161 is not activated, and Jane's frozen parent remains unchanged.
- No third-party independent custody, remote attestation, real host deployment, or autonomous learning is claimed.

## Next bound — JANE 163: The Witness to the Witness

Have independent custody roots sign receipt-window commitments. Compare signed sequence ranges and checkpoint heads across witnesses so missing suffixes and selective suppression become detectable against externally retained commitments.