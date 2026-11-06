# B180 — Deterministic Bounded Fuzzing Invariant

B180 moves beyond B178's 48 predefined mutations and B179's second parser. It deterministically generates 400 noncanonical input variations from the exact B161 template: **20 operators multiplied by 20 rounds**, using a fixed integer xorshift32 seed `0x180b179`.

The operators alter allowed YAML values, omit or duplicate keys, introduce unknown keys, aliases and interpolation, change or delete headings, inject HTML/script-like and active-URI patterns, alter the required redaction text and reproduction prompts, or introduce disallowed encoding anomalies. Every generated input is bounded at 9,216 UTF-8 bytes.

Both B177 and independently written B179 must accept the canonical control with identical semantics. Each generated mutation must be rejected by both with the exact specified error category. B180 HOLDs on **any** unexpected acceptance, parser disagreement, wrong error category, missing case, repeated case, changed mutation contract, malformed seed, or invalid report digest.

For reproducibility, the result includes the generator seed, operator and case identifiers, expected and observed decisions, a digest of all generated inputs, and a SHA-256 integrity digest for the full report. Up to twelve failing inputs can be preserved with the input hash, byte count and a bounded 320-character literal preview. These inputs are generated locally; never copy confidential target repository content into the previews.

**B180 is a finite seeded regression test, not a proof that no unsafe inputs exist.** Its success state `DETERMINISTIC_FUZZ_AGREEMENT_NO_EXECUTION` grants no PR creation, retry, branch, merge, or default-branch write permission. No downloaded repository code or target CI runs.

Three independent source witnesses remain a1/B168, b1/B169, and c1/B170. B180 supplies derived verification only: one observation layer, no quorum and zero ISA instructions.

## B181 next natural invariant
Implement counterexample shrinking for disagreements without weakening the original proof: preserve the exact failing input and produce a separately attested minimal reproducer, subject to strict step and size caps.
