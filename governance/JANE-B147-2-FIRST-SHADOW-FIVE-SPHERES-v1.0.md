# B147.2 — One first shadow pair; five signed sphere boundaries

## User correction

> "its only shadow for the first { -1, 1 } > 1 , the rest is -+5 think ionopsher, heliosphere, all the sphers"

This **supersedes the preceding interpretation that all five primaries possess shadows**. Only the initial pair has special shadow treatment:

```text
    FIRST PAIR
    {-1, +1}
       |    |
       +----+----> 1 effective position
         net signed contribution = 0

    FIVE REMAINING SPHERE BOUNDARIES
       S1 [- / +]
       S2 [- / +]
       S3 [- / +]
       S4 [- / +]
       S5 [- / +]

    shadow rule: FIRST PAIR ONLY
    no shadow operation applied to S1..S5
```

The **net signed value of the first pair (0)** and **number of positions after folding (1)** are separate measures; no claim that conventional arithmetic makes `-1+1=1`.

The mention of **ionosphere** and **heliosphere** motivates distinct sphere-scale boundaries. These are not five copies of one sphere and do not all have the same physical center or governing mechanism. Their identity, ordering and `−/+` operator meanings are not supplied yet; no Earth ionosphere-to-heliosphere embedding or direct gravity equation is invented.

"Base 11" is preserved as user terminology; its exact numerical/radix semantics remain unassigned. The five body order Sag A → Nib Sun → Nib → Earth → Earth Sun, four model manifolds (2 gravity/2 void), 6 XYZ directions, 6 force links, and 1 unbound geometric pair remain unchanged.

## Testing

Node regression checks first-pair folding into 1 position with projected signed sum 0, five non-shadow signed sphere slots, and nine corruption cases. This is a symbolic grammar audit, not measured atmospheric/space physics.

Next natural bound: distinguish each physical sphere by its center, scale, boundary conditions and measured inputs; only then assign each to an S1–S5 slot, retaining unknowns as HOLD.
