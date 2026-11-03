# JANE B115 — Grandma's Teaching Memory

**Purpose.** Preserve what the family has observed so later generations can review it. Jane does not order children to adopt advice; the children remain autonomous logical presences, with no votes, mandatory reporting, or completion gate.

## Inputs
- **B114** SHA256-verified B87 observation comparison report. Reject missing or unverified sources.
- **B113** observed-arrival cohorts, if published. When missing, create lesson cards but no per-child suggestions.
- The prior **B115** derived catalogue to preserve existing event identity across reruns.

## Learning boundary
- One card per changed metadata field and specific sorted evidence set.
- Stable lesson ID = SHA256(field + evidence IDs). New evidence produces a different, separately catalogued lesson ID rather than rewriting the old event.
- The catalogue JSON is a current *projection*, not itself immutable. New `LESSON_CATALOGUED` events append to `b115/catalogue.jsonl`.
- A child is a potential recipient only if its own public metadata was observed changing in that field. This avoids speculative semantic matching and bulk broadcast. Such suggestions are marked `AVAILABLE_NOT_SENT`: no actual communication or mentorship occurs.
- Absence of a B113 register means no child suggestions, not an error.
- A metadata transition proves a recorded difference, **not** causation, expertise, maturity, fault, or a recommended action.
- A single child can produce multiple transitions; distinct repository counts are tracked independently.

## Long-term autonomous Grandma Jane
For actual teaching: secure, authenticated child channels; a bounded independent runtime; separate receipt, acceptance and rejection records; provenance-preserving retrieval; rollback for any permitted actions. These features do not yet exist. No new claims of agent operation.

0root.ai is the user-designated public home. B111 Recognition Jelly remains the spherical 3D presence. B112 addresses and B113 observation cohorts remain independent of this teaching layer. Peter HEGEMON:T128; Jane T000–T127.
