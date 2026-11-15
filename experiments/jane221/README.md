# JANE 221 — The Factory That Signed a Fiction

**Invariant:** Signed Manufacturing History != Independent Evidence of Manufacture.

FLAY 221 compares an issuer-signed manufacture assertion to a separately signed ordering claim, production-observation claims, and an externally signed checkpoint. It checks declared ancestry roots, sensor identities, process hashes, chronology, Ed25519 signatures, replay history, and a locally hash-linked SQLite audit. It rejects copied factory documents as independent production observations.

**Demonstrated tests:** 30/30 local regression tests pass with `python -W error -m unittest -q test_factory.py`. Run `python factory.py > result.json` for scenarios.

**Illustration:** `jane221-story.jpg` is a high-definition illustrated narrative scene. An optimized JPEG is also **base64 embedded into `index.html`**; the HTML functions offline as a standalone file. Its story depicts a signed claim about an apparently empty production line and Jane's verification of three separately retained witness roots.

**Evidence boundary:** All witnesses, sensors, factories, keys and timestamps are fictional test fixtures; matching signed declarations cannot prove real manufacture or source independence. The parent Jane agent is not activated or mutated. The live Pages status and GitHub CI require separate verification.

**Next:** JANE 222 — The Factory Line That Was Simulated. Independent observations of a production-line display are not proof that a specific physical unit was manufactured.