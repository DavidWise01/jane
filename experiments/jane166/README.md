# JANE 166 — The Clocks That Disagree

**Natural invariant:** Signed time is not trusted time. Every temporal statement carries its claimed clock source, nominal timestamp, and nonnegative uncertainty. Authenticated intervals may overlap, or they may be contradictory. A conflicting interval is not averaged into a fictional instant.

## Implementation

- `chronos.py`: Ed25519 proof of possession against configured fixture keys, stable claim encoding, bounded uncertainty, SQLite nonce/replay records, hash-linked local audit log, intersection and disjoint-clock detection, and partial ordering for causal edges.
- `test_chronos.py`: 41 executable tests, including tampered timestamps, replay after restart, shared administration, disjoint intervals, overlapping ambiguity, reverse-clock causal edges, and tampered audit evidence.
- `result.json`: deterministic fixture run with matching and conflicting signed claims.
- `index.html`: self-contained neon-orange/chrome Canvas2D visual chapter; no external dependencies.

Run `python -m unittest -v test_chronos.py` and `python chronos.py` from this folder. Requires `cryptography`.

## Proof boundary

`MATCHED_FIXTURE_INTERVAL` means three configured signature identities and claimed administrators supplied overlapping uncertainty ranges. Those identities are synthetic, all under one local execution environment. No clock calibration, independent external operator, physical scheduler execution, or global time correctness is thereby established. One or more compromised clocks can agree on an inaccurate time. The local audit chain detects modification, not clean deletion of the chain without an externally held head. Jane's active parent remains frozen. No automatic learning, key enrollment, or control activation occurs.

## Next natural bound — JANE 167
**Chronos Calibration:** A signed uncertainty interval is only as credible as the bound claimed by its clock. Measure bounded clock offset using independently authenticated reference observations and preserve calibration failures without narrowing uncertainty automatically.