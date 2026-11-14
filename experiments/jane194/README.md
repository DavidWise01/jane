# JANE 194 — The Pattern of Missing Rounds

**Natural invariant:** A missingness pattern does not prove intent.

`missingness.py` freezes an ordered set of expected beacon rounds, publication deadline, and distinct declared observation roots before analyzing any reports. It keeps **all preregistered rounds in the denominator**, including unresolved rounds and observer outages. Two declared roots must report publication or post-deadline absence; opposite quorums are recorded as conflicting. Unknowns cannot be treated as observed absences.

The result records publication counts, post-deadline non-observations, unresolved cases, descriptive longest consecutive absence run, and an **optional binomial-tail sensitivity calculation** conditional on a user-declared baseline probability. The tail is calculated only on resolved rounds and is **not** a p-value for malicious withholding or a correction for observer selection bias. No baseline means no tail probability.

Synthetic demonstration: rounds 040–047, published 040,043,046; not observed after deadline 041,042,044,047; outage 045. Full denominator = 8, unresolved = 1, longest run = 2. `result.json` preserves these counts and analysis ledger state. Tests include observer conflict, missingness, source cardinality, malformed plans, deadline ordering, deterministic digests, and hash-chain tampering. The observation roots and commitments are **fixture declarations** and have not been authenticated against real external operators; this is a local analysis prototype, not real-world evidence of a beacon operator withholding output. Local hash chain does not reveal clean truncation unless its head is held separately.

Run `python -W error -m unittest -q test_missingness.py` and `python missingness.py`.

**JANE remains frozen**. The hive investigates; FLAY preserves what was observed without inventing intent.

## Next natural bound — JANE 195: The Observation Plan That Was Biased

Even a preregistered schedule can oversample particular rounds or rely on observers who share a network or incentive. The next gate should audit *why* rounds were selected, coverage across observation windows, and whether dropout depends on the measurement being audited.