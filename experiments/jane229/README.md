# JANE 229 — The Root That Claimed Independence

Invariant: **distinct claimed roots are not authenticated independent roots.**

This is a fail-closed, Ed25519 pinned-key fixture verifier. Each signed observation binds the same 256-bit claim digest and nonce to a signer, timestamp, and observe/abstain decision. Pins explicitly describe controller, platform, and source ancestry; root collisions are rejected as independent evidence. At least three distinct, currently active, non-colliding *declared* pin identities must sign before the verdict `DISTINCT_PINNED_SIGNERS_FIXTURE` can be reached.

The verdict deliberately **does not claim real independent accounts, secure key custody, hardware authenticity, or independently established operation**: configured pins and ancestry fields are declarations. Signing three statements with three programmatically generated keys is not three human witnesses. A signed `observe` or `abstain` is not a preference or authority to execute anything. No runner dispatch, live response, or Jane collective decision occurs.

## Local commands

```bash
python -m pip install -r requirements.txt
python -W error -m unittest -q test_root_auth.py
python root_auth.py --bundle empty-bundle.json --challenge nonce-unique-1234567890 --claim aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --now 2026-11-15T23:00:00Z --out result.json
```

The included empty input must return `NO_SIGNED_RESPONSES`, `UNRESOLVED`, and `action_executed=false`. The regression fixtures demonstrate correctly signed, wrong-key, stale, revoked, contradictory, reused and shared-ancestry cases, but **no real key has been enrolled**. The manual GitHub workflow has `contents: read`, runs the tests and the empty-bundle scenario, and uploads a receipt as a workflow artifact. The runner output must not automatically authorize any further action.

For physically independent witness accreditation, separately authenticate different controller accounts and security boundaries and obtain independently signed/pinned audit records. GitHub source commits alone cannot prove that independence.