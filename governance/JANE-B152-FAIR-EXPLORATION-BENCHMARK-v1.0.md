# B152 — Code Monkey Memory Against Round-Robin

## Invariant: measure before promotion
This bound compares the B151 memory score against a simple fixed round-robin policy under identical deterministic synthetic conditions. **Do not award a win on enthusiasm or majority vote.** Three witnesses `a1/b1/c1` run independently, with 12 decisions each; all source events are hypothetical B150 visual-unit readings.

Each target choice starts from the same radial position for that witness in each strategy. Five shell radii are `[20,30,40,51,62]` arbitrary display units. First visit to S3 and first two visits to S3 (two holds), and first visit to S5 (one hold), are determined solely by the scenario visit counter; later visits clear. The state is not a real ionosphere, particle orbit, gravity field or satellite trajectory.

Both traces record deterministic outcomes, their distinct witness IDs, cumulative distance, per-slot visits, independent HOLD traces and a hash-chain digest. The Node kernel uses native SHA-256; the browser demonstrates the same outcome and scoring but is not a cryptographic authenticator.

## Nominal scenario results (three witnesses pooled)
| Metric | Memory | Round robin |
|---|---:|---:|
| Coverage (unique shell/witness pairs; max 15) | 15 | 15 |
| Uncertain shell/witness pairs later resolved | 6 | 5 |
| Remaining unresolved uncertainty pairs | 0 | 1 |
| Repeated HOLD after initial HOLD | 3 | 3 |
| Travel, arbitrary visual units | 415 | 566 |
| Total decision budget | 36 | 36 |

**Nominal verdict: MEMORY_PARETO_DOMINATES** under the five predefined metrics, with three improved and two tied. This is a test-specific outcome, **not** a proof of globally superior strategy.

## Stress: ALL_HOLD
Set all slots to HOLD on their first 20 visits. Under the same budgets the memory policy focuses on unresolved shells, resulting in only 3/15 shell/witness coverage and 33 repeated HOLDs versus round robin's 15/15 coverage and 21 repeated HOLDs. Memory travels only 20 visual units versus 566. The stress verdict is **TRADEOFF_NO_UNQUALIFIED_WINNER**, because some metrics are better and some worse.

## Governing rules
- B147.2 first-pair shadow `{-1,+1}>1`; exactly five remaining signed sphere registers.
- B146.2 body order Sag A → Nib Sun → Nib → Earth → Earth Sun.
- Do not reinterpret displayed radii as physical distances or infer a verified time dilation.
- No quorum, no vote, no deletion of failed traces.
- Keep the B151 live scout memory and B150 observation journal unchanged: B152 is a **separate read-only benchmark display**, plus optional local export.
- A policy that cannot distinguish the nominal success from the stress failure is **HOLD**.

## Next bound
B153: independently detect retry loops and apply a minimum coverage guarantee before reattempting uncertain shells; compare over several unseen fixed-seed scenarios before claiming improvement.
