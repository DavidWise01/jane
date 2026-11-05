# B156 — D Dispatcher, Interrupt/Resume and Clean Pixel Arcade

## Canonical instruction organization

```text
[a:122 , b:122 , c:122 : d: a+b+c :: ISA]
        |
        d = dispatcher + read-only 366-address view
        |                    |                    |
        a/{H/a1}             b/{O/b1}             c/{N/c1}
        001..122             123..244             245..366
        Box62+Toroid60       Box62+Toroid60       Box62+Toroid60
```

B156 does **not** allocate a fourth 122-cell register or another shadow. Only the first `{-1,+1}>1` pair has the special shadow convention; five signed sphere registers remain nonshadowed.

## Dispatch contract

All commands enter through `d` with `via:'d'`. For reading and witnessing, either a global 001–366 address or an a/b/c local pointer/address may be used. `STEP` mutates only a named a/b/c program counter within 001–122 modulo 122 and appends one SHA-256-linked record; `READ`, `WITNESS`, `ASSEMBLE`, `CHECK` are observation/inspection instructions and append results but do not modify source cell data.

`INTERRUPT` freezes counter mutation and records a checkpoint of the three counters and dispatch count, including a cryptographic hash. A subsequent `RESUME` verifies the snapshot and continues from the preserved state; invalid checkpoints or unknown operations return HOLD without changing source addresses. The reference interpreter `audit()` reexecutes **every command from genesis** and compares each result against its stored event; a hash chain alone is not sufficient.

Three witnesses are independent, and there is no quorum. An interrupted scout's reports do not require another scout's approval.

## Layout

The Git Pages route `b156/index.html` replaces the cumulative stacked B149–B155 dashboard with a clean, self-contained mobile-responsive view. Left: large 320x200 pixel-art lab and crisp H/O/N box/toroid sprites. Right: compact ISA register controls and tabbed memory/audit. A derived D row shows 366 existing addresses, and the CPU trace uses a local session-only display. Browser demo logs are *not* cryptographically attested; Node SHA-256 is authoritative for the reference audit algorithm. No browser log is uploaded to GitHub automatically.

All 62/60 cells, H/O/N names, spheres and atom interpretation are conceptual geometry rather than experimentally validated elemental electron shells, gravity or clock-rate measurements.

Next: B157 persistent checkpoint proofs across browser sessions with explicit journal versioning, imported traces, and strict non-destructive migration from the B150/B151 journals.
