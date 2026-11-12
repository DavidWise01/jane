# JANE 137 — FLAY Chronos × Structure

Canonical fields:

```
{{ years.months.days}}{{hours.minutes.seconds}}{{degrees.arcminutes.arcseconds}}{{ anchor }}
```

Concrete example: `{{ 2026.11.12 }}{{ 07.18.00 }}{{ 123.45.56 }}{{ center }}`.

Three named groups of three anchors within a full 27-cell 3×3×3 lattice:
- Rear: upperleftrear (-1,+1,-1), centerrear (0,0,-1), lowerleftrear (-1,-1,-1)
- Center: centerupper (0,+1,0), center (0,0,0), centerlower (0,-1,0)
- Front: upperrightfront (+1,+1,+1), rightcenter (+1,0,+1), lowerrightfront (+1,-1,+1)

The nine anchors are **sparse named positions**, leaving 18 other lattice cells for future iterations. X = left/right, Y = down/up, Z = rear/front.

FLAY packs chronology, one angular measurement, spatial address, question, missing distinction, evidence digest and ancestry into deterministic review packets, then appends them to a hash chain. UTC offset is separate metadata because wall-clock times alone are ambiguous. An angle does not independently determine geographical position. GitHub and 0root.ai are one mirrored root, while public internet sources retain their original ancestry. Nothing automatically teaches Jane; missing roots request evidence, while resolved roots go to Jane review.

**Full locally executed implementation: 28/28 Python unit tests passed.** Repository includes a compact corresponding implementation and 14 regression tests, not separately executed in GitHub CI. The fully tested source, 28 tests, evidence packet, and enhanced interactive Canvas2D visualization are available as a conversation ZIP.

The hash chain requires an independently retained external head to detect clean truncation; coordinates do not establish causality, source independence, or authenticated clock time.
