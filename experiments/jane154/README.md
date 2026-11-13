# JANE 154 — The Edge of the Known Domain

**Invariant:** A verified finite domain is not a universal domain.

FLAY address: `{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ ancestor / child }}`.

A frozen ancestor is evaluated under a declared integer core domain, an outer state floor/ceiling, and a fixed maximum number of outward probes. FLAY tests A→B and B→A for validity and final-state agreement, preserving every trial in a deterministic hash-linked ledger. The core is evaluated first. Outward testing alternates left and right, stopping a side at its first incompatibility and continuing along the other side until budget or boundary exhaustion.

The fixture starts with `A = set(0)` and `B = nonnegative_add(0)`. Both orders commute over `[0,3]`. At `s = −1`, executing B first violates its precondition, while executing A first is valid. The right-hand states `4,5,6` remain compatible. The experiment tests exactly four additional states under a budget of six, because no more right-hand states remain within the declared ceiling.

**Result:** `BOUNDARY_COUNTEREXAMPLE`, first left failure at −1, none observed to the right within the tested range. This is not a proof of commutativity beyond the enumerated integers or a claim about continuous state spaces.

Run: `python -m unittest -v test_boundary` or `python -m unittest discover -s . -p 'test_*.py'`.

The local suite passed 36 tests. Evidence timestamps and source roots remain fixtures; no cryptographic time attestation or actual independent witness is claimed. The hash chain needs an externally held head to detect clean truncation. All output is review-only; Jane's active parent is unchanged.

**Next:** JANE 155 — Invariant Region: replace a list of compatible points with a proposed inductive condition, then search for a state transition that escapes that region. Never confuse finite testing with an inductive proof.
