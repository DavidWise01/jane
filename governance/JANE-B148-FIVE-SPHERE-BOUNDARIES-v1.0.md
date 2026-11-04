# JANE B148 — Five Signed Sphere Registers with Physical Identity Gate

## Governing invariant
Only the first pair `{-1,+1}` invokes the shadow operation, with net signed value **zero** and one resulting logical position. **S1–S5 are five separate signed boundary registers, not shadows.** The `- | +` sign meanings are deliberately unresolved.

```text
{-1,+1} > 1         SHADOW APPLIES ONLY HERE
   |
  net 0
   |
   S1 [-|+]      S2 [-|+]      S3 [-|+]
   S4 [-|+]      S5 [-|+]
     ALL FIVE PHYSICAL ASSIGNMENTS = UNBOUND
```

## Distinct sourced physical examples (candidates, not S1–S5 assignments)

| Physical example | Center | Boundary/identification | Source |
|---|---|---|---|
| Ionosphere | Earth | ionized upper atmosphere; NOAA typical ~80–600 km above Earth surface; time-variable | https://www.spaceweather.gov/phenomena/ionosphere |
| Plasmasphere | Earth | inner-magnetosphere plasma region; plasmapause varies | https://www.spaceweather.gov/phenomena/earths-magnetosphere |
| Magnetosphere | Earth | variable magnetopause, strongly asymmetric magnetotail | https://science.nasa.gov/heliophysics/focus-areas/magnetosphere-ionosphere/ |
| Heliosphere | Sun | solar-wind region and heliopause | https://science.nasa.gov/mission/voyager/fact-sheet/ |
| Astrosphere around HD 61005 | HD 61005 | external star's wind bubble; separate star system | https://www.nasa.gov/missions/chandra/young-sun-caught-blowing-bubbles-by-nasas-chandra/ |

These are **not strictly nested shells**, and "sphere" does not imply a perfect Euclidean sphere, constant physical radius, or shared center. The ionosphere's altitude range is approximate and not a sharp boundary. The Sun, Earth and HD 61005 have different frames and physical mechanisms. No exact radius is inserted for the other examples.

## Observation conditions to bind a real sphere to a slot
1. Named center and reference coordinate frame.
2. Dated, sourced observation and explicit environment/time.
3. Declared physical boundary criterion (e.g., plasma density, composition, pressure, magnetic-field dominance).
4. Units, range/uncertainty, directional dependence and spatial asymmetry.
5. Definition of what `-` and `+` indicate for that *specific* measured boundary.

Until all conditions are declared, proposed transitions return **HOLD** and the physical S1–S5 mapping remains null. Neither the four user-defined gravity/void manifolds nor the five corrected body referents becomes a physical law from those labels.

## Regression
The schema checker enforces exactly one shadow pair, five signed unbound slots, five example source records, preservation of Sag A → Nib Sun → Nib → Earth → Earth Sun, 2 gravity + 2 void, 6 signed directions, and ten deliberate mutation rejections. It is a deterministic catalog/logic validation only, not an experimental proof of physical gravity or timing.

**Next bound:** allow independent, dated observations to propose a candidate slot binding, but require its metric, source, and uncertainty before it can be promoted from HOLD.
