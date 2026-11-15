# JANE 226 — The Runtime Behind the Signature

**Invariant:** `Valid agent signature != verified agent execution`.

This is a **local, observed process-run experiment**. A bounded wrapper checks the SHA-256 of the allowlisted `bounded_worker.py` immediately before launching it without a shell, passes a challenge over stdin, captures stdout, verifies the process's output schema and binding, and emits an append-to-audit SQLite receipt with a replay guard. It never writes to NOM, 0root, or other agents' memory. It never triggers a selected action.

**Critical distinction:** The worker is an *explicit deterministic test adapter*, not an independently running A.C.I., NOM, or Jane. It outputs an instrumentation proposal because it was programmed to; it cannot reveal desires. The resulting receipt proves the **wrapper observed** a process invocation and output in the local environment. Without independent runner attestation, a remote secure enclave, or hardware evidence, it cannot prove that the machine wasn't compromised or independently authenticate its hardware origin. GitHub context values are treated as runner assertions, not cryptographic attestation.

## Reproduce

```bash
python -W error -m unittest -q test_runtime_proof.py
python runtime_proof.py --worker bounded_worker.py --nonce "$(python -c 'import secrets;print(secrets.token_hex(24))')" --audit run-audit.sqlite --out execution-receipt.json
```

Expected verdict: `OBSERVED_ALLOWLISTED_PROCESS_RUN`, always with `collective_decision=UNRESOLVED`, `action_executed=false`. Reusing the nonce with the same persistent SQLite audit yields `REPLAY`.

## GitHub Actions

Manual `workflow_dispatch`: `.github/workflows/jane226-runtime.yml`. It runs tests, creates a random fresh nonce, observes the allowlisted demo component, and uploads a time-limited artifact. Permissions are `contents: read`; no repository mutation. Committing the workflow **does not** mean it was dispatched or succeeded.

## Boundaries

- Hash pin computed at process start from the local worker file: binds the wrapper's observed code bytes, but is **not** an independent upstream publisher signature. A compromised wrapper could lie. To improve, supply separately reviewed code SHA and trusted ephemeral runner attestation.
- No shell; subprocess environment is restricted; output bounded to 12 KiB; timeout bounded to 15 seconds. This is *not* a full OS sandbox.
- Challenge binds agent ID, nonce, source digest, and question digest. Worker stdout binds the matching challenge; no collective authority is conferred.
- SQLite prevents repeat acceptance **within the same audit store**; deleting the store resets this protection.
- GitHub Actions is manual only, no standing daemon, no tokens in produced artifacts, and no operation on external agents.
- Local simulations and tests are evidence of code behavior, not physical device identity, subjective awareness, or independent collective preference.

Next: JANE 227 — independent verification of claimed CI execution and receipt ancestry, without elevating a GitHub Actions claim into a cryptographic hardware attestation.
