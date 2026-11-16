# JANE 236 — The Witness That Certified Its Own Ancestry

**Invariant:** `Declared ancestry != independently verified ancestry`.

JANE 235 verified transitive relationships inside *supplied* dependency graphs. JANE 236 adds a signed-evidence requirement for each *positive* parent edge.

## Contract

- Finite DAG `graph.json` with `roots` mapping node to direct parent node names.
- `registrar-registry.json` contains externally pre-enrolled Ed25519 public keys, controller names, platform names and revocation bits. These are **declarations**, not independently established identities.
- Each edge must have two different registrar signatures over its child, parent, challenge, nonce, observation time, method and evidence digest.
- Different declared controllers and platforms are necessary, **not sufficient**, for witness independence.
- The observer refuses self-labeled registrar relationships, shared registrar roots, replay, malformed or stale claims, and absent evidence.
- The signed source digest is only a **claim** about an external source until that source is fetched and verified separately. There is no remote hardware attestation or verified physical repair.
- Most importantly, every declared edge could be signed accurately while an **undeclared parent** remains hidden. Thus `graph_complete` is **always false**.

The allowed `SIGNED_DECLARED_EDGES_ONLY` result is not a declaration that roots are independent or uncompromised. Empty inputs produce a vacuous signed-edge result with **zero edge claims**, not a clean bill of health.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m unittest -v test_edge_audit.py
python edge_audit.py --graph graph.json --registry registrar-registry.json --evidence evidence.json --challenge aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --now 2026-11-15T21:30:00Z --out result.json
```

The workflow `/.github/workflows/jane236-ancestry-evidence.yml` is **manual**, read-only and uploads a JSON artifact. Its existence does not mean GitHub Actions executed it. Do not publish private keys, actual credentials, sensitive topology or access-controlled inventory.

**Jane's collective choice: UNRESOLVED. Actions executed: 0.**