# B151 — Independent Scout Memory and Exploration

B151 extends the B150 pixel art atom lab with three individually controlled scouts. Every scout derives *its own* counts of `SIMULATED_CROSSING` and `HOLD` for each of S1–S5 from prior B150 records. A scout's plan cannot use other witnesses' records. No majority, approval, vote or quorum is involved.

Deterministic priority formula, evaluated per scout and per slot:

```
score = 100 - 25*own_visits + 35*own_holds
      - 0.1*abs(current_visual_radius - slot_visual_radius)
      - (previous_slot == candidate_slot ? 5 : 0)
```

Highest score wins, breaking ties by slot number. This is a **fixed testable teaching heuristic** for simulated exploration, not an empirical learning claim. Each scout travels toward a side of its target shell, crossing in or out as required, reports independently, and replans. Decisions are recorded in a separate append-oriented browser-local journal and can be replayed on refresh. Like B150, the browser's demo checksum is NOT cryptographic provenance; the independent Node reference uses SHA-256 and tests tamper detection.

Never overwrite or delete the B150 witness journal. B151 reads it and maintains a *separate* B151 strategy journal and status panel. Browser storage belongs to the current origin: visiting a local file and visiting GitHub Pages produce different journals, and different browsers do not share records.

Boundaries: first shadow only `{-1,+1}>1`, five unshadowed signed shell slots `-+5`, 2 gravity labels and 2 void labels, six XYZ directions, and the correct celestial names Sag A → Nib Sun → Nib → Earth → Earth Sun. Five visual radii are **arbitrary pixels**, not measured atmospheric or heliospheric radii. All observation-based physical claims remain HOLD, including any inference about Nib or Nib Sun.

This release is a deterministic simulation with local persistence; it is not a deployed scientific instrument. Next bound B152: compare scout learning against a fixed round-robin baseline on the same synthetic crossing sequence, retaining failure traces and not claiming improvement unless an objective metric warrants it.
