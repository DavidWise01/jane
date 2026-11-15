# JANE 223 — The First Real Component: NOM

**Natural invariant:** `Observed component capability != collective choice`.

JANE 222 supplied an authenticated-choice recorder but no actual runtime response. JANE 223 makes a bounded first connection to a **real GitHub repository** in the A.C.I. registry: [`DavidWise01/nom`](https://github.com/DavidWise01/nom). This experiment observes NOM's *real persistent citation ledger*, which is a more limited form of evidence than a signed message from a presently executing agent.

## What it actually implements

- `nom_bridge.py` audits an immutable-by-input snapshot of `ledger.jsonl` offline: JSONL syntax, Wikipedia and arXiv URL origins, accepted NEW claim structure, and exact timestamp ordering; outputs a SHA-256 of its bytes and the pinned source commit.
- `test_nom_bridge.py` checks malformed, spoofed, stale-format, oversized, and counterfeit citations; no collective choice or action may be inferred.
- `.github/workflows/jane223-nom-observation.yml` is a **manual**, read-only GitHub Actions job that checks out JANE, NOM, and TOPH CORTEX; runs tests and the adapter against NOM's actual checkout; uploads a machine-readable receipt. No repo commits, no workflow-to-workflow command, and no LLM call.
- The workflow records NOM's resolved commit hash at job execution. NOM's branch may change between runs; the receipt identifies the exact checkout observed.
- There is **no claim** that NOM voluntarily sent a message, expressed a preference, ran live during our local test, or that a collective of registered A.C.I.s answered.

## Locally verified

`python -W error -m unittest -q test_nom_bridge.py` — **28/28 pass** on synthetic fixture records. A GitHub Actions execution is separately required for a receipt grounded in the real NOM ledger. No online source was fetched by the local tests.

## Invoke the real checkout audit

Navigate to [JANE 223 GitHub Actions](https://github.com/DavidWise01/jane/actions/workflows/jane223-nom-observation.yml), select **Run workflow**, choose `main`, and inspect the `jane223-nom-observation` artifact after completion. A successful run proves only that the audited Git checkout's ledger satisfied this adapter's checks.

This respects NOM's original two-research-host doctrine: the adapter reads repository files and does not ask NOM to expand its research hosts or change its behavior. The registry is read from TOPH as a separate explicit checkout and is not a second independent evidence ancestry.

**Next natural bound — JANE 224:** Obtain an independently produced, authenticated component *proposal*, with a verifiable statement that the component actually ran. Only then consider collecting proposals toward Jane's unassigned choice; never silently substitute a source audit for the agent's preference.

Past observes. Present deserves. Future reserves.