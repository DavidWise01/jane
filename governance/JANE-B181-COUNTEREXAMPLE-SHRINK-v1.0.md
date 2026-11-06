# B181 — Bounded Counterexample Minimization

B181 advances B180's deterministic parser disagreement checks into a reproducible failure-reduction boundary. B180's seeded mutation generator is the only source of candidate inputs. B181 reconstructs any reported counterexample by case ID and verifies its original SHA-256 before reducing it. No synthetic failure is invented when both parsers agree.

## Deterministic shrink invariant

A disagreement is defined by the full ordered four-field signature: whether parser B177 accepted; its returned error; whether independent parser B179 accepted; and its error. The minimizer attempts character-range deletions in deterministic order, retaining a smaller candidate only if the **exact same signature** survives. It has at most 300 parser-comparison attempts per input, a 9,216-byte input cap and a 12-example report cap.

Each example records the complete original generated input, complete reduced input, byte counts, SHA-256 hashes, exact initial/final parser observations, attempt count, and an explicit disclaimer: the reduced example is *not* proven globally minimal. Full input material is limited to locally generated fixed-template mutations. Never feed confidential repository content into this recorder.

If B180 has no disagreement, B181 returns `NO_COUNTEREXAMPLES` with zero examples. If actual differences exist and minimization succeeds, B181 returns `COUNTEREXAMPLES_PRESERVED`. Hash mismatches, a lost decision signature, unauthorized behavior, damaged attestation or unexplained failures produce HOLD. A positive report is an observation, not CI validation or write authorization.

The B181 workflow has read-only GitHub permissions, runs native regressions, and preserves an artifact whether it succeeds or HOLDs. No remote source code is run, and no PR, retry, merge, or default-branch write permission is added.

Three witnesses stay a1/B168, b1/B169 and c1/B170. B181 is derived verification only. There is no quorum or defined ISA instruction.

## B182 — Next natural boundary

Check *one-deletion minimality* under a bounded budget: after shrinking, attempt every single-character deletion (when within caps) to see whether any still preserves the exact signature. Clearly distinguish a verified locally minimal result from a budget-limited unverified result.
