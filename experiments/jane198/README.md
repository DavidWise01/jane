# JANE 198 — Correlated Missingness

**Invariant:** Distinct hidden-cause mechanisms can generate the same observed evidence. Observational equivalence is not causal identification.

## Engineering result

`causal.py` constructs two illustrative deterministic structural-causal fixtures with latent binary `U`, outcome `Y=U`, and a candidate-specific selection gate `R=1 iff U equals gate`. Both project to identical observed data: 16 preregistered rounds, eight observed outcomes, five successes, eight missing. Their hidden outcomes differ, yielding population success rates 31.25% vs 81.25%. Neither is inferred as true.

`FLAY198.compare` validates each candidate projection against the immutable observation set, reports compatibility and different candidate rates, and withholds causal identification. The append-only local SHA-256 event chain is tamper-evident within the local fixture only. No external witness, physical process, crypto authentication, or automatic learning is claimed.

## Test

```sh
python -W error -m unittest -q test_causal.py
python causal.py > result.json
```

Tests cover malformed observations, mismatched structures, model equivalence, conflicting hidden estimates, observational bounds, deterministic projection, audit-chain tampering, and unchanged frozen parent.

## Viewer

Open `index.html` to inspect 16 outcomes, choose latent models A/B or overlay, and see how changing unobserved values does not change recorded evidence.

## Next natural bound

**JANE 199 — The Proxy That Pretends to Measure the Cause.** A proxy for the unobserved common cause may be measured imperfectly, with errors correlated with outcome or selection. A proxy-based identification claim requires explicit accuracy and validation evidence.