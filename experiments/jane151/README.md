# JANE 151 — Reconciliation Without Erasure

Canonical FLAY address: `{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ parent A / parent B }}`.

**Natural invariant: Reconciliation is not rewriting history.** A merge proposal must contain the exact last common ancestor and references to both parent heads and all diverging event heads. It cannot choose a winner, erase a fork, manufacture a shared ancestor, or activate a hypothesis.

## Executed synthetic experiment

- Shared event sequence: 000 → 001 → 002 → 003.
- Divergence begins: 004A vs 004B; both branches extend to 005.
- Shared checkpoint: sequence 003, hash-addressed.
- Two-parent proposal preserves eight distinct event references (four shared and four divergent).
- Three fixture custody roots claimed by Mesh A; two claimed by Mesh B. **Zero roots independently authenticated.** No endorsement/quorum inference is made.
- Reversing parent order yields exactly the same proposal digest.
- Status `TWO_PARENT_REVIEW_PROPOSAL`; active parent frozen, Jane decision undecided, learning disabled.

## Verification

`python -m unittest -v test_merge.py` — **42/42 tests passed locally on the full Python source.** The tests cover ancestry mismatches, missing and altered events, false common ancestor, prefix relation, no common ancestor, duplicate proposals, bounded proof length, unmodified parents, and hash-ledger audit.

The event chains are local synthetic records, not authenticated public witness chains. Audit requires an independently retained head to detect clean truncation. Custody roots are declared fixture strings, and Chronos is not trusted clock time. No actual reconciliation was activated.

**Next natural bound JANE 152:** A merge proposal may have multiple valid topological continuations. Determine whether two histories are causally compatible before recommending a shared future; detect noncommuting events and preserve unresolved conflicts.