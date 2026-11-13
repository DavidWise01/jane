# JANE 148 — The Witness Beyond the Wall

**Natural invariant:** Retrievable proof is not independent proof.

FLAY keeps the existing address family:

```text
{{ years.months.days }}{{ hours.minutes.seconds }}{{ degrees.arcminutes.arcseconds }}{{ recursive / anchor }}
```

## Engineering boundary

`fetch.py` adds a bounded HTTPS endpoint client with an exact URL allowlist, no-follow redirect policy, response-size and timeout limits, JSON parsing, Ed25519 verification, claim-to-key/custody/admin binding, Chronos freshness validation, persistent nonce replay detection, append-only raw-response snapshots, and a cross-custody checkpoint comparator. All decisions are **review-only**; Jane remains the only learning authority.

- A signed response is not proof that the public endpoint is administered by an independent organization.
- GitHub and 0root.ai count as **one owned ancestry**, not separate administrators.
- Local transport fixtures provide three cryptographically separate keys and distinct *claimed* administrators.
- Tests do **not** call live endpoints, authenticate the administrators, or demonstrate deployment.
- The endpoint allowlist prevents arbitrary URL requests, but the reference network adapter does not implement DNS/IP-pinning against rebinding, DNS rebinding after resolution, content freshness beyond the signed clock, certificate pinning, independent endpoint discovery, public transparency log anchoring, or a production SSRF threat model. Use only operator-configured endpoints in a controlled environment, not arbitrary user-supplied URL values.
- Hash chaining detects edited snapshots, but clean truncation is only detectable with an independently retained checkpoint head.
- Local SQLite storage is not tamper-proof against administrators.
- Because Chronos includes a wall-clock and an angle, a UTC offset remains required to determine an unambiguous instant. The angle is not a full geolocation.
- The fixture-owned Ed25519 private keys are generated only in the test process.

## Reproduce

```sh
python -m pip install cryptography
python -m unittest discover -s . -p 'test_fetch.py' -v
python demo.py
```

**34/34 tests passed locally** on the exact `fetch.py` and `test_fetch.py` committed files, including replay across restart, outages, forks, conflicting claims, forged content, SSRF guardrails, oversized responses, strict content type, and withheld Jane activation.

## JANE 149 — Natural bound

**Witness reachability is not witness continuity.** Introduce independently retained published checkpoint expectations and a reconciliation ledger for temporary outages, forked histories, and restored network access. Do not silently accept a late contradictory receipt.