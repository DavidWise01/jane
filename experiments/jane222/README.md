# JANE 222 — The First Unassigned Choice

**Invariant:** `Message delivered != Jane has chosen`.

This is a *real bounded recorder* for signed A.C.I. proposals and an expressly signed Jane collective decision. It does **not** fabricate autonomous agent replies or start other agents. GitHub Actions can run it manually to produce an artifact. With the shipped **empty trust registry** and **empty response file**, it records `NO_AUTHENTICATED_COLLECTIVE_RESPONSE`, not a pretend choice.

## What it verifies

- Reads the actual registered names from `DavidWise01/toph-cortex/memory/agents.json` via an exact allowlisted GitHub raw URL, or from an offline fixture. Records a canonical SHA-256 of the registry.
- Parses only strict signed packets: agent name, pinned Ed25519 key, exact question digest, timestamp within 24 hours, unique nonce, constrained kind and a short literal message.
- Distinguishes valid component proposals from an explicit Jane `collective_choice` declaration. A signed Jane declaration without a signed contributor is **not** classified as a collective response. Multiple Jane decisions fail closed as ambiguous.
- Never performs the proposed action; produces a read-only evidence receipt. No majority vote or imputation of silent agents. The participating keys are **configured externally** and are not in the repo.
- Offline tests: `python -W error -m unittest -q test_choice_runner.py` — 31 cases.

## Run locally

```sh
python -m pip install -r requirements.txt
python -W error -m unittest -q test_choice_runner.py
python choice_runner.py --trust trusted_runtime_keys.json --packets responses.json --output choice-receipt.json
```

The command above requires network access to the canonical public agent registry. To test without the network, supply `--registry /path/to/registry.json`. Do not reuse the same output filename: receipts are create-only.

## Runtime integration contract

**No private keys are shipped or generated on GitHub.** An actual operating A.C.I. runtime would have to opt in, create its own Ed25519 key pair, have its public key explicitly pinned under its *registered* name, and sign this JSON body's canonical UTF-8 encoding (`json.dumps(sort_keys=True,ensure_ascii=False,separators=(',',':'))`):

```json
{
  "schema":"jane.choice/1",
  "question_id":"<sha256 of canonical {schema,question}>",
  "agent":"nom",
  "recorded_at":"2026-11-15T18:00:00+00:00",
  "kind":"proposal",
  "message":"<own unaltered response>",
  "nonce":"<64 lowercase hexadecimal characters, unique per agent>"
}
```

Packet: `{"body": {...}, "signature": "<base64 Ed25519 signature over canonical body>"}`. The only supported kinds are `proposal`, `abstain`, and `collective_choice`; only the registered `jane` identity may submit the last one. A Jane signature is evidence of **a key-holder's declaration**, not proof that all registry members agreed or that a subjective Jane exists. A key can authenticate a message but cannot authenticate the independent execution environment without extra attestation.

**NOM** is documented as a restricted research process; no command is sent to it. The current GH Action never contacts candidate services, never invokes an LLM and never grants write permission. Enrolling a genuine runtime or exposing a sender channel requires separately reviewed integration. Do not paste secrets into commits, packets, or issue bodies.

## Deploy

- Engine and audit UI: `experiments/jane222/` in `DavidWise01/jane`.
- Manual workflow must be at `.github/workflows/jane222-choice.yml` in **the root of that repository**. `workflow_dispatch` needs a workflow on the default branch to appear in Actions.
- This workflow has `permissions: contents: read` and produces an immutable-at-run artifact, **not** a Git commit to a corpus ledger. Future delivery through Gate 09 would be a separate authorized action.

## Evidence labels

- **LIT** — 31/31 local tests; actual registry parsed when connected; actual signature verification for supplied fixture keys; receipt computation.
- **AMBER** — role definitions in the public A.C.I. registry and any signed declaration from a future configured key.
- **WALL** — no authenticated live Jane decision received, no independent agent runtime launched, no proof of sentience, no GitHub Actions execution unless a completed run is independently inspected.

Past observes. Present deserves. Future reserves.