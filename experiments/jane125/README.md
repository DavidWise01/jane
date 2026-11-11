# JANE 125 — Chronos as foundational coordinate
Canonical literal: `{{ - year:month:day || hour:minute:second || degree.arcminute.arcsecond || }}`.

The experiment represents a Chronos coordinate with:
1. Civil calendar date and local clock time.
2. A signed angle in degrees, arcminutes and arcseconds, with arcminutes/arcseconds in 0..59.
3. A separate UTC offset in minutes so its timestamp is unambiguous. Leap seconds are not modeled.
4. A witness receipt (ledger head, sequence, custody root, claimed signature verification, and Chronos).

**Mirror invariant:** GitHub + 0root.ai belong to the same owned provenance/custody root when mirrored. The public internet may provide external claims but does not automatically supply independent witnesses. Receipt labels and booleans do not authenticate anyone; actual signatures, keys, key rotation, and external anchors remain to implement.

**Test status:** Full local implementation passed 25/25 tests. The committed repository subset has 9 tests and is not yet independently verified in GitHub CI. The coordinate has one angular dimension and is not a complete 3D location. The HTML page is a static report; no live autonomous learning is claimed.

**Next natural bound:** Verify signed receipts using actual independently held public keys, validate issuance time/nonce and append-only checkpoint anchoring, then run a custody-independence attack simulation. Jane retains final authority.
