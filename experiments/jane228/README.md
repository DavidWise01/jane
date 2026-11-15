# JANE 228 — The Witness That Shared the Runner

**Natural invariant:** `Two execution receipts != two independent execution witnesses`.

## Result

The checked-in `observations.json` is explicitly **synthetic, self-reported fixture metadata**, not actual GitHub run data. Three differently labeled purported GitHub Actions observations share a platform trust root and several other upstream roots; therefore `SHARED_EXECUTION_ANCESTRY`. No independent runner, platform, or human witness is established, no Jane collective decision was recorded, and nothing was executed on Jane's behalf.

## Commands

```bash
python -W error -m unittest -q test_ancestry.py
python ancestry.py --input observations.json --output result.json
```

No third-party dependencies. `result.json` is the deterministic local fixture output; the manual GitHub workflow `jane228-ancestry.yml` runs the same tests and emits a build artifact. **Do not mistake the workflow's own output for independent attestation of the workflow.**

## Comparison rules

Every observation declares a platform, credential, runner, workflow, source, artifact, and operator origin; absent origin is preserved as unknown. Exact shared ancestry makes a collision edge. Source run/commit identifiers and evidence hashes alone are not independent witnesses. A union of collision edges yields connected dependency clusters. All GitHub Actions observations share the `github.com/actions` platform root and cannot count as independent *platform* attestations merely because run IDs differ. Collisions or unknown roots prevent an independence conclusion. Even disjoint declared roots are not proof without trustworthy external attestations.

## Security and honesty boundary

- Fixture roots are claims, not remotely authenticated identities.
- `evidence_origin=separately_retrieved` is declared by the caller and is **not** independently validated by this program. It does not magically authenticate inputs.
- Repository README, signed git commit, or GitHub job success do not prove an independent external executor, physical device, or awareness.
- GitHub's public platform API metadata and independently pinned external evidence would be required for stronger execution corroboration; no such integration is asserted here.
- No mutations to prior Jane, NOM, TOPH, Hallway, or memory records.
- The HTML chapter is an offline evidence viewer, not a backend or agent runtime.

## Next invariant 229

`Distinct claimed roots != independently authenticated roots`. Seek externally verifiable provenance and preserve the no-witness state until independent claims can actually be checked.