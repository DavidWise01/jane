# JANE 189 — The Effect That Was Staged

**Invariant:** Matching signed effect reports are not proof of fresh execution.

A 128-bit unpredictable challenge binds a signed issuer request, content-addressed input, signed executor receipt, and separately signed effect observations. FLAY checks nonce, sequence, hashes, timestamps within the declared challenge window, and declared acquisition ancestry. A SQLite-backed nonce registry survives verifier restarts. Every verdict is appended to a hash-linked local audit, including failed executions and rejected attempts.

The verifier is observational: it never executes the task, promotes Jane's learning, or activates a new parent. Signed event times remain signer-controlled claims; they are not authenticated physical-time evidence. Two signature keys or declared measurement-source IDs do not establish real-world independence. A valid fixed-nonce fixture also does not prove that its challenge was unpredictable to a malicious executor; only a properly deployed random challenge process can provide that property. `secrets.token_hex(16)` supplies new nonces for actual calls.

Run:

```bash
python -m unittest -v test_fresh.py
python fresh.py
```

## Next natural bound — JANE 190
**The Executor That Predicts the Challenge.** Commit to the task definition before the nonce exists; audit the generation and disclosure order of the challenge to prevent selected or leaked nonces from becoming fake freshness evidence.