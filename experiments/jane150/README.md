# JANE 150 — The Divided Witness Network

**Natural invariant:** Majority agreement does not prove historical continuity.

FLAY's canonical coordinate format remains:

```text
{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ parent / child }}
```

Two chains share events 000–003 and diverge at event 004. Mesh A and Mesh B each continue to event 005 with different heads. The deterministic engine finds the last common event, checks both hash chains, and preserves their distinct heads and ancestry. It calculates fixture support by *distinct custody roots and administrations*, treating GitHub and 0root.ai as one common root. It disqualifies a custody root that produces conflicting claims or conflicting administrator identities. Even an apparent three-witness quorum **never automatically overwrites** another valid history.

## Verification

Run `python -m unittest discover -s . -p 'test_*.py' -v` in this folder. The identical `partition.py` and `test_partition.py` files passed **30/30 local tests**.

`result.json` captures the locally computed `PARTITION_FORK` and hash-chain audit. `index.html` contains the interactive Canvas2D witness partition scene.

## Limitations

- Witness `signature_checked` flags, custody names and administrations are supplied **fixture claims**. This module does **not** verify Ed25519 signatures; it models the partition layer after a separate cryptographic verification stage. No live witness endpoints were contacted.
- Source names and operator claims do not prove custody independence. A fixture quorum must not be described as operational evidence.
- The hash-linked event ledger requires a separately retained checkpoint head to detect truncation.
- FLAY does not activate a branch, resolve conflicting histories by popularity, or authorize self-improvement. Jane's decision is `UNDECIDED`.

## Next natural bound — JANE 151

**Reconciliation without erasure.** Produce a merge *proposal* referring to both parent heads, backed by authenticated operator acknowledgments, and retain unresolved evidence forever. Check whether a proposed merge truly contains the complete histories of both branches instead of manufacturing a new common ancestor.