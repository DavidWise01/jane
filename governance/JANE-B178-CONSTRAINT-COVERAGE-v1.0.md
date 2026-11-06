# B178 — Fail-Closed Semantic Constraint Coverage

B178 tests the B177 fixed-template semantic validator at its **constraint boundary**, rather than interpreting a single accepted template as sufficient coverage.

## Canonical test obligation

The accepted positive control is the exact B161 bug-report template. The negative controls consist of 48 named mutations, partitioned into 15 field cases (each of the five fixed YAML keys: changed, duplicate, removed), 12 Markdown heading cases (each of six headings: changed and removed), four grammar cases, twelve unsafe-body and content cases, and five encoding/size cases.

For each mutation, B178 calls the B177 semantic parser and demands the **specified error category**; rejection under a different error category also HOLDs. The matrix additionally requires its complete fixed list of case IDs exactly once and rejects incomplete, duplicated, substituted, weakened, and unexpectedly accepted fixtures. The source and output must record both the expected and actually observed failure categories.

The positive state is `CONSTRAINT_COVERAGE_PASS_NO_EXECUTION`. The output includes full case rows, group counts and an SHA-256 integrity digest, then is saved as a workflow artifact. Missing or weakened regression coverage, a parser that accepts a known-negative fixture, a parser that rejects the canonical positive control, or an invalid digest yields HOLD.

## Limit of the evidence

Forty-eight regression mutations are a *finite test matrix*. They do not prove that every unsafe YAML or Markdown expression has been enumerated, nor that a text file is generally safe outside the exact B161 template. B178 tests the semantic validator without running any GitHub repository code. It performs no GitHub API writes and grants no draft PR, retry, branch, merge, or default-branch write privileges. It does not assert target-repository CI passed.

B178 is a **derived read-only validation**. The original source witnesses remain a1/B168, b1/B169 and c1/B170, with d derived and unprivileged. There is no vote, quorum, or new ISA instruction.

## B179 natural boundary

Add mutation-hardening and adversarial parser differential checks: independently parse the five-key YAML grammar in a second implementation and compare accepted structures against B177, while keeping canonical exact-byte enforcement and fail-closed status.
