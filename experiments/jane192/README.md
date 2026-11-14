# JANE 192 — The Future Randomness Beacon

**Invariant:** Public randomness is not automatically unmanipulable randomness.

`beacon.py` freezes a task and selects one exact future beacon round. The verifier checks a signature under a configured beacon key, signed release chronology, freshness, fixed-round identity, SHA-256 commitment to the entire beacon receipt, two distinct *declared* fixture administrative roots, persistent task replay, and same-round signed equivocation. It derives a domain-separated challenge from the task, beacon ID, round number, and beacon randomness.

The log is locally hash-chained and can detect alteration but requires an externally held head to detect valid suffix truncation. Test keys are deterministic and not suitable for production. Signed timestamps are assertions, not trusted clocks. The code does not fetch a live public beacon, establish proof of secrecy, prove randomness is unbiased, or authenticate independent real-world custody. Its protection against beacon choice is limited to rejecting a different round from the frozen task; a withheld selected round remains unavailable, with no fallback to a more favorable round. The active Jane parent is unchanged.

## Run

```bash
python -W error -m unittest -v test_beacon.py
python beacon.py
```

## Next natural bound — JANE 193

**The beacon operator who withholds:** Model publication windows, unavailable rounds, independently witnessed non-publication evidence, and anti-selection rules for fallback rounds. No proof of nonexistence should be manufactured from a failed network fetch.