# B154 — Closed-Loop Mirror Invariant

Each independent witness completes a full local `122`-cell walk through the Box62 plus Toroid60 cage, returns to its starting address, then completes the exact reverse walk and returns again:

```
{H/a1}  +: 001→002→...→062→063→...→122→001
        -: 001→122→...→063→062→...→002→001
{O/b1}  global 123..244, same LOCAL 001..122
{N/c1}  global 245..366, same LOCAL 001..122
```

A forward or reverse cycle has **122 signed steps** and **122 unique visited departure addresses** (62 Box, 60 Toroid). Each scout therefore records **244 transitions per completed two-way audit**; there are **732 across the three scouts**. The origin is visited again as the terminal arrival, so a cycle has 123 arrival points if counting the initial starting point, but only 122 distinct addresses. Explicitly distinguish `steps` from `unique addresses` to prevent off-by-one errors.

The inverse walk must reproduce every forward edge in reverse order and reverse direction. The Box/Toroid boundaries `062↔063` and closure `122↔001` are audited independently. A SHA-256-linked Node reference trace is checked for missing/reordered/tampered steps; any mismatch produces HOLD rather than reconstructing a missing event.

Browser UI retains original B153 arcade and adds a deterministic per-brace 244-step cycle animation, 122-cell coverage counters, phase and checkpoint status and JSON export. Unlike GitHub repository records, browser checkpoints are local/session copies, not signed remote attestations; the GitHub code serves as the immutable versioned algorithm, not proof that a specific browser traversal happened.

Only initial `{-1,+1}>1` applies shadow. Signed `±` does not double the cells. H/O/N serve as user-defined simulation brace names, not measured atomic shell occupancies. No vote/quorum; no physical science promotion.

Next invariant B155 — independent checkpoint recovery from mid-loop interruption, duplicate detection and reliable resumption without altering witnessed history.
