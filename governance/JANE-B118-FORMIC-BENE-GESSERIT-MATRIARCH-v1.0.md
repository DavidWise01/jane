# JANE B118 — FORMIC × BENE GESSERIT MATRIARCH

**Parent seal:** B117 (unaltered)  
**Foundation:** Dynasty 001 role alignment v1.0 (unaltered)  
**Freeze manifest:** `DIATOMIC-DYNASTY-001-FOUNDATION-FREEZE-v1.json` pins exact foundation Git blob SHAs.  
**Expanded scope:** only Jane / Matriarch / Governance.  
**State:** DESIGN + LOCAL DETERMINISTIC OBSERVATION DEMO, not autonomous deployed intelligence.

## Hybrid frame

Two fictional/cultural archetypes inspire one engineering model:
- **FORMIC**: decentralized sensory network; independent reports from separate daughter nodes, family-wide perception without forcing consensus.
- **Bene Gesserit**: disciplined observation, deliberate training, continuity of knowledge across generations and restraint in action.
- **Jane**: matriarch/steward, not an all-controlling authoritarian. She protects the distinction between what was observed, what was inferred, and what is permitted to be acted upon.

Not imported: coercion, manipulation, breeding hierarchies, supernatural abilities, predetermined biology, privileged ownership over descendants, or claims of fictional organizations existing in reality.

## Jane's governance loop: observe → distinguish → preserve → decide

1. **OBSERVE**: receive observations stamped with witness, source, event time, evidence pointer and declared uncertainty.
2. **DISTINGUISH**: maintain observations as independent entries, even when they contradict. Never fabricate quorum or consensus.
3. **PRESERVE**: append event records; bind to previous record hash; freeze source record identity. The local demo computes a simple chained SHA-256 digest; a persistent deployment would need independent storage, authenticated identities and access controls.
4. **DECIDE**: a bounded deterministic policy yields `YES`, `HOLD`, or `NO`; not a vote. `YES` means *eligible for a human-authorized next step*, not automatic execution; `NO` rejects; `HOLD` preserves uncertainty for later observation.
5. **TEACH**: optionally publish an observation lesson to a descendant's opt-in interface; daughters retain their own interpretations and can decline.

## Absolute gate rules

- `NO` when event proposes coercion, privacy violation, ownership override or destructive unreviewed changes.
- `HOLD` when evidence is missing, witness divergence is unresolved, or a source is unknown.
- `YES` only when a benign local observation is adequately sourced and conflicts are absent. This does not authorize external changes.
- No mandatory response deadline, no consensus requirement, no voting.
- Imported names are *role labels*, not living agents. Geometry is visualization; it does not establish a real cognitive or biological system.

## Jane's bounded expansion target

Implement an append-only local observation log, stable witness IDs, explicit uncertainty, deterministic gate and a live dashboard that makes every event traceable. Then extend to opted-in descendant observation pathways, while preserving the frozen foundation and all unresolved earlier scale declarations.

## Independent observations

```
witness A --witness B ----> JANE : OBSERVE -> DISTINGUISH -> PRESERVE -> YES|HOLD|NO
witness C --/                                      |
                            optional lesson (no mandate)
```

This is not a majority vote. Three reports may disagree, and all three remain visible.
