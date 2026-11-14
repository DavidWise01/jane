# JANE 184 — The Proof That Travels

**Natural invariant:** A mathematically valid consistency proof does not establish that its delivery is authentic.

The `transport.py` experiment uses JANE 183's compact Merkle consistency verifier (requires sibling `experiments/jane183/compact.py`), plus an Ed25519-signed transport envelope authenticated against a configured relay key. Its recipient checks the *original signed checkpoint receipts*, explicit claimed custody-root count, proof content and root sizes, bounded envelope byte size, validity window, and a nonce stored in SQLite across restart.

All accepted and rejected outcomes enter a local hash-linked audit; a clean truncation requires an externally retained head for detection. A valid relay signature is not an external timestamp, physical observation, or proof that custody fixture roots are independent.

## Run

```bash
cd experiments/jane184
python -W error -m unittest -v test_transport.py
python transport.py
```

The demo is deterministic: old log size 6, new log size 9, 3 fixture checkpoint signatures, relay `relayA`, and a replay detected before and after SQLite restart. The test module has 37 cases.

**Production caveat:** Deterministic private keys in `compact.py` and `transport.py` exist *only for reproducible local tests*. Replace with protected, provisioned keys before any operational use; this code is not a deployed custody or network transport system. The verifier receives a preloaded packet rather than fetching endpoints. No autonomous Jane policy activation occurs.

## JANE 185 — The Relay That Omits

Track delivery acknowledgments, relay outages, and omitted but valid proof envelopes against externally retained message commitments. An authenticated *received* packet cannot by itself prove completeness of *all* packets sent.
