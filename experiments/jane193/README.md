# JANE 193 — The Beacon That Withholds

**Invariant:** An unpublished round is not proof of manipulation. Signed absence is a report about one observer's view, not universal non-publication.

This experiment freezes a specific future beacon round and its publication deadline. The verifier checks Ed25519-signed beacon output and signed observation reports for context, time, nonce replay, and declared ancestry. It records bounded fetch attempts without substituting the next available round. An overdue round with signed `NOT_OBSERVED` reports becomes `NOT_OBSERVED_BY_FIXTURE_QUORUM`; a transport failure is `NETWORK_UNAVAILABLE_OR_WITHHELD`, not a claim of malicious suppression.

The code uses a persistent SQLite nonce ledger and a hash-linked audit. It does not anchor that local audit externally. All keys, roots, operators and availability data are synthetic fixtures, not independent live services. Each status expresses verification of recorded claims, not physical availability or intent. Jane's active parent is frozen.

Run `python -W error -m unittest -v test_publication.py` and `python publication.py`.

Next natural invariant **JANE 194 — Selective Publication Across Rounds:** one missing round does not establish bias. Compare a preregistered sequence of rounds and observation schedules, preserve missingness, and prevent sampling only successful releases.