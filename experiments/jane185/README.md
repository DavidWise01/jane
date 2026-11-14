# JANE 185 — The Relay That Omits

**Natural invariant:** Authentic delivery does not prove complete delivery.

FLAY verifies a sender-signed outbox manifest containing ordered per-message SHA-256 commitments, then independently authenticates receiver-signed acknowledgments for each exact sequence and payload commitment. The relay is untrusted, and its selected subset cannot certify completeness.

The bounded audit separates `DELIVERY_COMPLETE_FIXTURE`, `DELIVERY_PENDING`, and `SELECTIVE_SUPPRESSION` using the declared observation deadline. Missing acknowledgments are evidence of missing acknowledgments, **not conclusive proof that the relay caused message loss** (receiver downtime is another possibility).

The fixture signs messages 1, 2, 3, delivers acknowledgments for 1 and 3, and audits at 1500 ms against a sender checkpoint issued at 1000 ms and a 300 ms observation deadline. Expected outcome: `SELECTIVE_SUPPRESSION`, missing sequence `[2]`.

The signed manifest binds epoch, nonce, issued time, total size, full ordered manifest and content hashes. The receiver signs sequence, payload hash, receipt time, and nonce. SQLite persists nonces and accepted acknowledgments. A local hash-linked event log remains vulnerable to complete truncation unless an independent head is retained. All signing keys are deterministic synthetic fixtures; they do not establish independently operated physical custodians or transport execution.

To run:

```sh
python -m unittest -v test_delivery.py
python delivery.py
```

**Limits:** This implementation verifies complete expected sequence coverage for a signed snapshot, rather than proving that the sender has revealed its latest outbox head. Temporal deadlines rely on fixture clock values. Jane's active parent is frozen; no learning or activation occurs.

## Next natural bound — JANE 186
The acknowledgment that arrives late: distinguish delayed acknowledgments, receiver outages, and definitively missing messages with independently witnessed sender/receiver watermarks and clock uncertainty.
