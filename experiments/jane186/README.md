# JANE 186 — The Acknowledgment That Arrives Late

**Invariant:** An overdue acknowledgment is not proof of message loss.

`reconcile.py` verifies Ed25519 signatures on sender outbox entries, receiver acknowledgments, watermarks and outage reports. The deterministic reconciliation rule uses signed clock uncertainty ranges, an explicit deadline, and signed receiver watermarks. A missing ACK beyond a watermark is an **evidence gap**, not a verdict about packet loss or relay intent. Outage intervals are treated as an uncertainty boundary. A later receipt can classify actual acknowledgement timing as on time, late, or time-uncertain.

**Limitations:** Reports use synthetic test signing keys and declared clock frames. The verifier's `reconcile` function consumes receipts previously checked by `FLAY.receive`; callers must not supply unverified receipts. A signed receiver watermark is a claim from a configured key, not proof of receiver completeness, physical delivery, or real-world time authority. Local hash-linked history alone cannot reveal clean truncation without an externally held head. No Jane activation or learning occurs.

Run: `python -m unittest -v test_reconcile.py`, followed by `python reconcile.py`. The 36-test suite includes outage overlap, nonce equivocation, restart-safe replay, malformed receipts, and deadline uncertainty.

## Next natural bound — JANE 187
**The Watermark That Cannot Be Trusted:** Authenticate watermark coverage with an independently auditable receiver sequence commitment and detect equivocation between purported complete ranges.