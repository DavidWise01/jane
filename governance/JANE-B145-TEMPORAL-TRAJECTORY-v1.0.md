# JANE B145 — Time, Velocity, Trajectory, and Separate Clock Rates

**Bound:** Explicitly attach `t` and `(v_x,v_y,v_z)` to the B144 `(x,y,z)` coordinate frame. Preserve signed XYZ directions, four named gravity/void categories, and five named referents without guessing their actual coordinates or velocities.

## Independent fields

```text
FRAME: LOCAL_INERTIAL_REFERENCE
  POSITION    [x,y,z]       meters
  VELOCITY    [vx,vy,vz]    meters/second
  TIME        t0 -> t1      seconds, dt>0
  AXES        +/-x +/-y +/-z
  MANIFOLDS   G0 G1 V0 V1   classifications, no metric assigned
  REFERENTS   sag a | nibaru sun | nibaru | earth | earth sun
```

## Deterministic model
For a declared constant velocity in a single inertial frame, `Δr=vΔt`; speed squared `v²=vx²+vy²+vz²`, and an ideal Minkowski-frame clock obeys:

```
dτ/dt = sqrt(1 - v²/c²), for 0 <= v² < c²
Δτ = Δt sqrt(1-v²/c²)
c = 299792458 m/s
```

This is a textbook **special relativistic** comparison of inertial worldline segments, not a new discovery and not a full prediction for moving clocks around black holes. The numerical examples (rest, +x at 100 m/s, -z at c/2) are synthetic. Matching endpoints is a consistency check only when constant velocity is independently asserted.

**Time dilution / frame boundary:** Do not simply multiply B144 stationary Schwarzschild rate by B145 inertial special-relativistic rate without deriving both from the same local frame and metric. A common coordinate time and integrated worldline are necessary. The B145 combined gravity-and-motion output stays HOLD.

## Negative controls
- Missing or nonmonotonic frame timestamps.
- Speed >= c.
- Wrong frame ID.
- Invalid or contradictory endpoint.
- Comparing clocks over unequal time windows.
- Attempting to promote combined gravity/void motion into verified physics.

## Next
B146 — define a physically explicit metric and measurement comparison for known celestial cases, with no hypothesis promoted as an astronomical fact.
