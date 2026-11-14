# JANE 181 — The Timestamp That Cannot Be Backdated

**Natural invariant:** A signed timestamp does not prove the first real-world observation. A cryptographic inclusion proof establishes only that a supplied entry belongs to an authenticated log snapshot.

## Experiment
- `transparency.py`: domain-separated SHA-256 binary Merkle tree; root commits to exact number of leaves; explicit inclusion path; Ed25519-signed checkpoint receipts; configured administrative-ancestry quorum; persistent SQLite nonce/replay, rollback, same-size fork and linked growth checks; hash-linked local audit records.
- `test_transparency.py`: 46 offline regression tests including size-binding regression, proof tampering, missing entries, extension, rollback, conflicting heads, signer replay and SQLite restart.
- `result.json`: actual local demo output.
- `index.html`: standalone Canvas2D view of witness and tree topology; no external scripts.

**Scope:** All keys and administrators are synthetic local fixtures. Claimed observation timestamps are signed assertions, not externally trusted time. The `minimum_observed` input is a supplied bound, not an independently authenticated timestamp. `prev_root` checks a signed link but does not alone prove that the new log is a true append-only extension of the old *entry sequence*; full prefix comparison or consistency proof is required for that. A local hash chain can be truncated if its final head is not held externally. This experiment does not verify physical scheduler execution, real-world custody independence, or unforgeable first observation.

Run: `cd experiments/jane181 && python -m unittest -q test_transparency.py`

JANE remains the decision authority. FLAY is an observation/audit mechanism. No automatic learning or activation.

## Next natural bound — JANE 182
Prove append-only **consistency between signed tree roots**, not merely a claimed `prev_root` link, and compare externally retained checkpoint heads.