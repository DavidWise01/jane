# JANE 253 — The Destination That Ignored the Fence

**Invariant:** `Valid Fencing Token != Fenced External Side Effect`.

This experiment fixes the common TOCTOU bug where a worker checks a fencing token before beginning work but commits after its ownership has been revoked.

## Demonstrated protocol

1. A destination stores `(resource, epoch, holder)` in its own SQLite database.
2. `grant` atomically advances epochs. Lower or conflicting epochs fail.
3. `commit` checks the **current epoch and holder inside the same `BEGIN IMMEDIATE` transaction** that inserts the effect. A worker's earlier `precheck()` never authorizes the write.
4. Repeated operation IDs are idempotent for an identical payload/epoch/holder and conflict otherwise.
5. Rejected attempts are preserved in a separate audit table; no losing-epoch effect is committed.

The synthetic demonstration performs `precheck(A,1)` → `grant(B,2)` → `commit(A,1)` → `commit(B,2)`. Result: `FENCED_STALE_EPOCH` for A and `COMMITTED` for B.

## Reproduce

```bash
python -m unittest -v test_destination_fence.py
python destination_fence.py --db demo-destination.sqlite --output result.json
```

Python 3.10+; standard library only. `jane253-destination.yml` is a **manual** read-only GitHub Actions workflow and uploads tests and evidence as artifacts.

## Evidentiary and operational limits

- These are locally simulated hosts sharing **one destination authority**, not independent GitHub/Railway deployments.
- SQLite transactions enforce this specific destination, not arbitrary HTTP APIs, email, payments, Git pushes, or other services which may ignore tokens.
- A stale worker can still perform an external irreversible side effect unless the **recipient** atomically checks epoch and writes its effect, or an equivalent reliable gate/intermediary controls the effect.
- Fencing epochs are trusted inputs to this local prototype; no quorum certificate, external signer verification, or durable distributed coordinator has yet been integrated.
- This shows a protected-destination commit boundary, not global exactly-once behavior, consciousness, independent agent desires, or an authorized collective choice.
- No real agent chose or executed a task. `collective_choice` stays `UNRESOLVED`.

## Next natural invariant — JANE 254

`One fenced destination != All downstream side effects fenced`.

A transactionally accepted task can launch effects in another system that does not understand the epoch. The next test should introduce an outbox and destination-verified effect consumers, with fault injection between commit and delivery.