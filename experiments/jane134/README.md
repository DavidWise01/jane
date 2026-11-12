# JANE 134 — The Authentic Witness

Canonical Chronos: `{{ - year:month:day || hour:minute:second || degree.arcminute.arcsecond || }}`.

Replace self-asserted verification flags with **Ed25519 signature checks** over canonical JSON containing: key ID, nonce, Chronos, UTC offset, sequence, chain head, and claim digest. The receipt is rejected for invalid signatures, unknown or revoked keys, stale Chronos, duplicate nonces, or mismatch with its trusted custody-root checkpoint.

GitHub and 0root.ai remain **one owned custody/provenance root**. Quorum requires three distinct custody roots; three signatures from one custodian do not suffice.

## Tested
16/16 tests passed on the full local source using cryptography 46.0.4. The committed source mirrors this prototype, with a separate 12-test CI-ready subset. Re-run via:
```sh
python -m pip install cryptography
python -m unittest discover -s experiments/jane134 -p 'test_*.py' -v
```

## Security limitations
The registry of allowed keys, custody mapping, and checkpoint anchors are supplied trusted *fixtures*. The prototype does not independently authenticate custodians or fetch/check external anchors. Nonce replay detection is process-local and resets at restart. Chronos is a claimed timestamp, not a trusted hardware time source. Signing keys are generated ephemerally; none are deployed. Do not treat the local quorum as independent real-world attestation. No automatic Jane learning.

## Next natural boundary — JANE 135
Persist replay state, rotate keys without erasing old verification history, and anchor checkpoint heads to genuinely separate administrative domains with auditable receipts.
