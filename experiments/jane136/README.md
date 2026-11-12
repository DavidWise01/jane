# JANE 136 — The External Memory Anchor

Canonical coordinate: `{{ - year:month:day || hour:minute:second || degree.arcminute.arcsecond || }}`.

The full local prototype was executed against 20 tests, all passing. A six-event hash-valid chain matched three signed Ed25519 fixture receipts. Rolling back to a four-event, still hash-valid prefix yielded **ROLLBACK_DETECTED** because the external checkpoint receipts retained sequence 5 and the later head.

**GitHub/0root.ai share one owned root**; two other roots must represent genuinely independent custody to claim three-witness operational verification. In this experiment the keys, roots and checkpoints were all generated locally; there is no deployed independent custody.

The committed Python files are a compact reproduction with eight tests, not the identical 20-test locally executed version. Full versions are also available as conversation downloads.

To run: `python -m pip install cryptography && python -m unittest discover -s experiments/jane136 -p 'test_*.py' -v`.

Limitations: the compact verifier checks Ed25519 signature and checkpoint continuity but does not validate Chronos as a trusted clock, use persistent replay state, or retrieve anchors from authenticated independent services. The full local verifier includes more input validation, nonce checks, and Chronos freshness rules. Neither provides real-world custody independence. Jane learning remains disabled.

## JANE 137 — next bound
Authenticated network custody: independently operated witness endpoints, signed checkpoint publication, anti-equivocation checks, replay-resistant storage, and recovery policies when receipts disagree.
