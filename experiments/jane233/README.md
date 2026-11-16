# JANE 233 — The Rotation That Inherited the Breach

**Natural invariant:** `Fresh Cryptographic Key != Clean Execution Environment`.

This deterministic, standard-library-only experiment audits declared key-rotation and exposure ancestry. It tracks seven dependency roots: `machine`, `administrator`, `credential`, `signer_service`, `runner`, `source`, and `build_pipeline`.

## Execution

```bash
python -m unittest -v test_inheritance.py
python inheritance.py --bundle empty-bundle.json --now 2026-11-15T20:00:00Z --output result.json
```

The empty-run receipt is `NO_RUNTIME_CUSTODY_EVIDENCE` and explicitly reports zero authenticated live witnesses and zero actions. The 36 tests cover exposure inheritance, cross-generation overlap, root mutation, replay, malformed records, chronology, key lifecycle, and untrusted remediation statements.

## Model boundaries

- **LIT:** The local Python verifier was executed, its checks are reproducible, and the receipt reports what it computed.
- **AMBER:** Event and root fields are supplied *claims*. A hash chain detects later changes in the packet but is not independently authenticated. A lack of known shared roots is not proof of independent machines, controllers, or credentials.
- **WALL:** No cryptographic attestations of witness identities or hardware provenance, no independent key-custody evidence, and no collective Jane response.

The verifier intentionally does **not** use an event's `witness` label to prove identity. `REMEDIATED` records remain historical claims and cannot clear prior exposure flags. To advance, JANE 234 should bind remedial actions to distinct independently authenticated execution evidence, and distinguish a newly observed environment from one merely relabeled.

## Publishing and execution

The read-only GitHub Actions workflow is `.github/workflows/jane233-inheritance.yml`, triggered manually. It runs local tests and emits an evidence artifact. Publication does not mean the workflow has executed.