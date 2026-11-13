# JANE 159 — Guarded Forces and Reachability

**Invariant:** A transition contributes to an unboundedness argument only when its guard permits the required sequence. FLAY models nondeterministic integer transitions with explicitly enumerated guard semantics and immutable audit records.

The guarded increment `s ↦ s+1` iff `s < 20`, starting from zero, has a complete reachable state set `{0,…,20}` and satisfies the declared `[0,20]` bound. The unconditional increment is enabled at every integer and has an algebraic witness for unlimited positive motion. The local search returns the explicit `20 → 21` violation. Incomplete bounded exploration yields `INCONCLUSIVE_BUDGET` unless a counterexample has already been found.

The explorer checks every enabled successor on visited states. Proof of closure is restricted to the declared integer-additive model. No live network witnesses, external proof, automatic training, or claim of real-world independence is made. The hash-linked local ledger is not immune to deletion without an externally retained head. All tested programs are synthetic local models.

Run `python -m unittest discover -s . -p 'test_*.py' -v` in this directory.

Next JANE 160: Fairness and liveness—an infinite enabled path is distinct from an inevitable outcome when other choices remain available.
