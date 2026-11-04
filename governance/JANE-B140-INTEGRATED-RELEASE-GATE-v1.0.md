# JANE B140 — Integrated Release Gate

## Purpose

Close the B117–B140 **design sequence** without declaring the larger science, runtime, or deployment finished. B140 is a **release candidate with fail-closed status** until GitHub Actions produces an inspectable all-pass run.

## The gate

```text
B127 ... B139 (13 required tests)
        |
        v
EXECUTE IN CLEAN NODE 22 CHECKOUT
        |
        +-- Any test missing/failed? --> HOLD
        |
        v
CROSS-MODULE INVARIANT AUDIT
        |
        +-- Any failed? -------------> HOLD
        |
        v
WRITE MACHINE REPORT (CI ARTIFACT)
        |
        +-- Success != peer review/physical validation
        |
        v
RELEASE ELIGIBLE FOR SOFTWARE-RULE FREEZE
```

Running `node scripts/btf2/jane-b140-release-audit.cjs` runs all 13 test files and seven cross-invariant checks; missing files, thrown errors or failed checks cause a nonzero exit code. It emits `b140/audit-report.json` with file hashes and results. CI should upload that report even on failure. **Do not commit generated audit reports**: time-varying CI output belongs in run artifacts. The static JSON manifest intentionally remains `HOLD` until a verified run establishes a matching result. Success does not retroactively convert the static manifest into an attestation.

The B139 browser viewer remains a static fixture-based audit view. Browser end-to-end interaction, durable journal storage, data ingestion from live ENSDF, empirical validation and independent attestations remain open.

## Release semantics

- `COMMITTED`: source and workflow exist in repository.
- `STATIC VERIFIED`: source existence/expected feature strings verified.
- `CI PASS`: actual GitHub Actions job confirms the runner ran and exited zero.
- `BROWSER VERIFIED`: actual browser checks for B139 controls and snapshots.
- `SCIENTIFIC VERIFIED`: quantitative references and empirical claims independently examined against published data.
- `PRODUCTION READY`: explicit persistence/security/operations acceptance.

These stages are **not interchangeable**. The bounded roadmap count can be 24/24 source milestones while the release is still on HOLD.

## Foundation unchanged
Two analytical cubits, 8 seats each, 15 earned archive references, C1:111 Nexa as the only Royal Purple active seat; channel order RED, BLUE, GREEN, BLACK, WHITE, GRAY, YELLOW, ROYAL PURPLE. Old append-only boundary documents are not overwritten.

## Next stage
B141: browser-to-kernel data adapter with explicit read-only provenance; B142: durable chained witness storage and independently verifiable attestations.
