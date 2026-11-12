# JANE 145 — Independent Custody

**Natural invariant:** `Three signatures ≠ three independently operated custodians.`

FLAY Chronos address: `{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ upperleftrear / center / upperrightfront }}`.

This experiment verifies Ed25519-signed checkpoint receipts, validates declared custody roots and administrator labels, checks Chronos freshness, prevents nonce replay, preserves signed disagreements as append-only events, and compares consensus checkpoints to a local ledger. Github and 0root.ai count as **one owned origin**. Key rotations and mirrors do not create additional independent sources. One root claiming different administrators is quarantined.

## Verified local experiment

**33/33 Python unit tests pass.** The demo assembles three locally generated test keys in registry-labeled `owned:canonical`, `external:A`, and `external:B` roots, all signing checkpoint sequence 7. The local state is sequence 5, resulting in `ROLLBACK_DETECTED`. A full fixture agreement at sequence 7 produces `MATCHED_FIXTURE_QUORUM`. A single custodian's contradictory receipts produce `EQUIVOCATION_QUARANTINE`; different custodians disagreeing produce `CROSS_ROOT_CONFLICT`. Three keys under the same administrator do not reach quorum. There is no automatic learning; Jane remains undecided.

Run `python -m pip install cryptography && python -m unittest -v test_custody.py` from this folder.

## Crucial security boundary

This does **not** prove real independent control. All private keys, administrator labels, public-key registrations, and custody-root assignments originate in one synthetic local fixture. A registry value `operator:A` is only a claim. No third-party witness endpoint, authenticated admin attestation, or externally retained checkpoint is deployed. Replay state is in memory and would reset with this prototype. A local hash chain needs an externally retained head to detect valid truncation. Signature validity establishes key possession, not truthful claims or independence.

## Next: JANE 146 — Authenticated custody enrollment

Define an independently administered enrollment and attestation protocol. Require explicit operator enrollment, rotate keys under their original custody root, persist replay and checkpoint state, and only change `independent_operators_verified` after independently checking documentary or network-based evidence. Treat uncertainty as unverified, not as assumed independence.