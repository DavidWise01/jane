# B133 — Changing-Environment Revalidation

**Invariant:** yesterday's PASS is immutable evidence, never unconditional approval for a new context.

## Boundary

- Every trial has immutable `id`, `configuration`, `environment`, `evidence`, `gates`, optional `origin` (any earlier observation), optional `parentAccepted` (only an already-promoted trial with same configuration).
- Five independent gates: nuclear, chemical, environmental, provenance, repeatability. Each is PASS/FAIL/UNKNOWN.
- Any FAIL → REJECT; any UNKNOWN without FAIL → HOLD; all PASS → PROMOTE.
- Old trial decisions are never rewritten. A new environment starts UNTESTED even if an older environment passed.
- The latest recorded trial for a specific configuration/environment determines *current* authorization in that context, including a later HOLD or REJECT that suspends previously established eligibility.
- The `active` map is a historical register of all promoted trials, **not a current-environment permission ledger**. Authorize only with `current(configuration,environment).authorized`.
- A new PASS after HOLD is a fresh observation, not retroactive validation of failed states.
- Genealogy distinguishes `origin` (can reference a failure that motivated adaptation) from `parentAccepted` (may only reference an accepted prior record).
- Every append is SHA-256 chained and deep-frozen in process. This is not durable persistence or tamper-proof attestation outside the process.

## Executed local test

Five artificial Kr-84 test trials:
1. `KR84-SEALED` → PASS in sealed-container context.
2. `KR84-OPEN-UNKNOWN` → HOLD in different context.
3. `KR84-OPEN-FAIL` → REJECT in that context.
4. `KR84-OPEN-PASS` → PROMOTE after an independent assessment.
5. `KR84-OPEN-RETEST` → HOLD on missing repeatability; latest state is not authorized.

Expected audit: five observations; two promoted; two held; one rejected. The original sealed-container record remains eligible. Duplicate IDs and rejected-parent inheritance are prohibited.

**Test result:** the included Node.js test passed in the local creation environment. Gate states are mock supplied values, not nuclear experiments, chemical risk assessments, or empirical claims about open-air krypton behavior.

## Scope

This extends B132 append-only without rewriting it; previous B117–B132 records remain unchanged. No new agents, no quorums and no physical actuation. The logical trainer models constrained decisions, not natural evolution or scientific truth.
