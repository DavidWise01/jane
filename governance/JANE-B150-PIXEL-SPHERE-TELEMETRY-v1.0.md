# B150 — Pixel Monkey Scout Walk, Signed Sphere Readings and Local Replay

B149.2's atomic 3D projection is retained but B150 creates a **new versioned Pages route** at `/jane/b150/`. Three original pixel-monkey witnesses (a1, b1, c1) now physically move *within the simulation scene* through the five signed visual boundary radii. An outward crossing is recorded only when the before reading plus measurement uncertainty lies strictly inside and the after reading minus uncertainty lies strictly outside; inward crossing applies the inverse inequality.

In the browser, crossing records are persisted to **localStorage on that browser and origin**. They are not pushed to GitHub or remotely synchronized. The journal is append-oriented: resetting the animation only resets coordinates, while clearing the display does not delete journal entries. Reload and Replay rebuild the visible audit from the saved entries. Export JSON preserves them. Browser records use a chained **FNV-1a-style demo checksum** strictly for accidental-change detection, not tamperproof provenance; no untrusted source may treat it as a digital signature. Quota/private-mode failures leave the simulation running but show `LOCAL PERSISTENCE UNAVAILABLE`.

Independent Node reference logic instead calculates SHA-256 over canonical JSON entries and validates the chain upon replay, rejecting altered evidence. The browser and Node journal hashes are **not interchangeable**.

Signed observation requirements: event ID, witness identity, slot, frame, source, timestamp, before/after values, threshold and uncertainty, direction. Missing provenance, ambiguity and claimed physical evidence without attestation all return HOLD. Synthetic clear crossing returns **SIMULATED_CROSSING** only.

**One shadow pair only:** `{-1,+1}>1`, signed net zero. Five `S1–S5 [-|+]` remain non-shadow signed shell registers. All render radii are arbitrary demonstration units and do not represent physical ionosphere/magnetosphere/heliosphere radii. No physical clock rate is inferred or promoted.

No quorum; each witness records independently. Preserve five celestial model referents in order Sag A → Nib Sun → Nib → Earth → Earth Sun.

Local test command: `node scripts/btf2/test-jane-b150-pixel-sphere-telemetry.cjs`. Pages route expected `https://davidwise01.github.io/jane/b150/` if GitHub Pages deployment serves that path.
