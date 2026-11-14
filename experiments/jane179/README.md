# JANE 179 — The Authority Whose Key Is Compromised

**Invariant:** A valid Ed25519 signature is not proof of uncompromised authority.

The experiment combines a SQLite hash-linked event ledger, authenticated compromise claims from two configured distinct recovery roots, automatic quarantine for newly submitted actions from compromised keys (including backdated submissions), and signed recovery to the next key epoch. Existing decisions remain in the historic ledger, while inherited grants require review. Successful fixture recovery does **not** automatically activate Jane or certify physical custody independence.

## Reproduce

```bash
python -W error -m unittest -v test_compromise.py
python compromise.py
```

## Limitations

All cryptographic keys are deterministic, synthetic test fixtures. Do not use this seed derivation in production. A signing key cannot attest reliably to its own theft. The compromise cutoff and recovery roots are approved fixture *claims*, not externally verified compromise evidence. Timestamps alone do not prove execution order. A local hash-linked log requires an independent externally retained head to detect valid suffix truncation. Grant-lineage review is conservative and is not automatic retrospective revocation of historic acts.

## FLAY coordinate

`{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ center }}`

## Next natural bound — JANE 180
**The Historic Decision After Compromise:** Once a compromise is discovered, determine whether old signed actions are historically authentic, potentially attacker-authored, or supported by separate pre-compromise custody checkpoints. Preserve all three categories without retroactively inventing certainty.