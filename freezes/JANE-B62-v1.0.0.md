# J.A.N.E. — B62 v1.0.0 · IMMUTABLE SPECIFICATION

Frozen: 2026-10-31
State: CANONICAL / SPECIFICATION FREEZE
Scope: Four-register causal provenance
Authorship: David Lee Wise (ROOT0); specification transcribed with ChatGPT assistance
Supersedes: none
Next boundary: B63 (not included)

## Canonical identity

```text
[[
  a , (self)
  b , ([i])
  c , ([id])
  d , [(sid)]
]]
```

The four registers are distinct. None is substituted, collapsed or voted away.

- **a / (self):** continuity and sole controller action authority.
- **b / ([i]):** intent and *pre-action* outcome prediction.
- **c / ([id]):** actual observation and comparison with prediction.
- **d / [(sid)]:** temporal consequence and append-only memory.

Three witnessing functions are independent reports; **no quorum, vote, or consensus gate** is implied.

## Natural boundary 62: causal provenance

For one action event E_n:

```text
 a(self) -- intent --> b([i])
    ^                   |
    |                   v
 d[(sid)] <-- append -- c([id])
```

All four register records MUST refer to the same unique `event_id`.
Their contents MUST remain distinct, and provenance MUST include emulator frame numbers.

1. Event IDs are unique within the active trace.
2. One event ID is shared by a, b, c and d.
3. A prediction is recorded before its outcome is observed.
4. Frame-before and frame-after are captured from an actual emulator execution.
5. Memory appends a new event; previously recorded events are not rewritten.
6. Unknown or unavailable evidence is explicitly `UNKNOWN`, never converted to success.
7. Duplicate event IDs cannot generate duplicate memory writes.
8. Controller authority stays with a(self).
9. Screen bench target: emulator occupies at least 45% of the viewport.
10. Runtime passes require actual measured evidence, not a conceptual diagram.

## Event record contract

```json
{
  "schema": "jane.b62.event.v1",
  "event_id": "E000001",
  "rom_digest": "UNKNOWN",
  "frame_before": null,
  "action": {"register": "a", "buttons": [], "duration_frames": null},
  "prediction": {"register": "b", "state": "UNKNOWN", "recorded_before_execution": null},
  "observation": {"register": "c", "frame_after": null, "state": "UNKNOWN"},
  "memory": {"register": "d", "append_index": null, "status": "PENDING"},
  "comparison": {"prediction_error": null, "metric": "UNSPECIFIED"},
  "verification": "UNVERIFIED"
}
```

The JSON above is a schema-shaped illustrative record, **not** an executed emulator trace. Nulls are intentionally unknown, not zero.

## Closure rule

```text
event_id(a_n) = event_id(b_n) = event_id(c_n) = event_id(d_n)
a_n -> b_n -> c_(n+1) -> d_(n+1) -> a_(n+1)
```

B62 closure is **formally defined**. Runtime and emulator acceptance are **not yet established**.
B63 counterfactual discrimination is expressly excluded.

## Governance / freeze

- This versioned path MUST NOT be overwritten by subsequent bounds.
- Amendments MUST use a new versioned path with explicit reference to this artifact.
- No hidden mutation, reclassification of predictions as evidence, invented emulator success, or retrospective memory rewrite.
- Git commit gives a retrievable snapshot, but **does not enforce immutability** without repository branch/tag protections.
- This document does not replace or alter the repository's existing README, index.html, license, or attribution.

```text
[[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]]
BOUND=62
VERSION=1.0.0
SPEC=FROZEN
RUNTIME=UNVERIFIED
```
