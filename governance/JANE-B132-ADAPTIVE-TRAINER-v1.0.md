# JANE B132 — Adaptation Without Inheritance of Failure

**Natural bound:** A failed candidate may inspire a new experiment; its failed state never becomes an accepted parent.

## Generation rule

```text
OBSERVE CANDIDATE IN ENVIRONMENT E0
          |
          +-- FAIL: append record F0, do not promote
          |
          +-- ADAPT: create NEW immutable ID F1
                        |
                change context/configuration
                        |
                   re-run all gates
                        |
                PASS -> active pool
                FAIL -> failure journal
                UNKNOWN -> HOLD
```

**Separate two links:**
- `origin`: the earlier observation that *motivated* the retry. May point to a failure, because failures remain teachable evidence.
- `parentAccepted`: an independently validated prior active configuration from which inheritance is allowed. Must never point to a rejected/held trial.

This is an explicit **genealogy of ideas**, not a biological claim that organisms or people with undesirable traits should be excluded. No real genetic experiments or chemical manipulations are instructed or automated.

## B131 case progression

- KrF2 room temperature: fails an environmental persistence gate. A *different* KrF2 cold-storage candidate may pass the defined persistence gates in a suitable environment; its identity is new, and the prior failed record remains unchanged.
- Rb85 metal in water: fails environmental/chemical suitability. A separately evaluated inert-storage candidate may pass the specified retention context. This is not an endorsement of handling reactive metals.
- Kr85: chemically quiet but radioactive; a missing or unknown nuclear safety claim remains HOLD, not upgraded by changing the container.

## Deterministic gates

`nuclear`, `chemical`, `environment`, `provenance`, `repeatability`, each **PASS / FAIL / UNKNOWN**:
- Any **FAIL** -> REJECT.
- No fails but at least one **UNKNOWN** -> HOLD.
- All **PASS** -> PROMOTE.

The kernel validates supplied gate results, rather than measuring or verifying experimental nuclear and chemical properties. All event IDs are unique; observations are deep-frozen in-process and chained by SHA-256, but no persistent storage or external attestation is built in. The active accepted-pool can only contain all-pass records.

## Constitutional invariants

1. Observed failures are never deleted or silently corrected.
2. An adaptation has a new immutable ID and its own evidence and environment.
3. The unsuccessful origin is a **witness**, not an accepted inherited parent.
4. No quorum, no votes, no compulsory action.
5. B117–B131 and the two-cubit 16-cortex dynasty remain unchanged.
6. No physical simulation, chemical safety qualification or independent experimental validation is claimed.

## Test contract

Six mock trials: 2 rejected, 1 held, 3 promoted. Additional tests reject a failed parent, duplicate trial ID, missing evidence, and unknown gate state. Tests inspect both the immutable failure and the independently promoted retry.
