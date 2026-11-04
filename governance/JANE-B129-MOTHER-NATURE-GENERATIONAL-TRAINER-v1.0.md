# JANE B129 — Mother Nature Generational Trainer / Failure Retained, Not Inherited

**User rule:** "It's mother nature math, it works until it doesn't work through this generational trainer, a failure is not introduced into the gene pool."

## Design invariant

```text
PROPOSE → OBSERVE → CHECK → PRESERVE REPORT
                         |
                    ALL GATES PASS?
                     /          \
                   YES           NO
                    |             |
            PROMOTE CANDIDATE   RECORD FAILURE
             TO ACTIVE POOL     KEEP OUT OF POOL
                    |             |
              NEXT CYCLE       STOP THAT BRANCH
```

A *gene pool* here is the set of **accepted simulated configurations**, never actual genetic selection or decisions about people. A failure is not erased or hidden; its observation, provenance and reason are retained in the append-only witness journal. No failed configuration is passed as an accepted parent to the next cycle.

## Four gates

1. **Conservation** — verify domain-specific conservation / constraints (e.g., mass number and charge for a declared nuclear-reaction model).
2. **Stability** — meet explicitly defined lifetime or persistence threshold for the target context. Note: physically transient intermediates can still be scientifically meaningful, even if they are not selected as *stable Grandma*.
3. **Provenance** — reliable observation and source support.
4. **Repeatability** — documented repeatability or evaluated evidence appropriate to the phenomenon. The B129 demonstrator accepts externally supplied booleans; it does *not itself measure* these physical facts.

If any gate is absent, hold the candidate outside the active pool. For the simple deterministic implementation, failure of any mandatory gate results in `RETAIN_FAILURE_ONLY`. Missing evidence does not imply the candidate is intrinsically worthless.

## Mother Nature analogy: boundaries

Natural evolution does not flawlessly reject every harmful change or always choose an objectively best outcome. Biological populations can carry harmful variants, and fitness depends on environments. **The strict nonpropagation rule is this trainer's deliberate engineering selection policy**, not a statement that nature literally works this way, and not a rule for selecting human beings.

## Implementation

`scripts/btf2/jane-b129-generational-trainer.cjs`: bounded candidate evaluator; SHA-256 chained append-only witness events (in-process, not persistent or tamper-proof storage); promotion of all-pass configurations only; auditor rejects membership of failed candidates in active pool.

The B117 seal, lineage, two analytical cubits, sixteen-cortex quarter-codon, and existing documented nuclear-reaction registry remain unchanged. No real-world nuclear physics or genetic process is autonomously controlled.
