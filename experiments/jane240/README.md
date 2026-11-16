# JANE 240 — The Provider That Certified Its Own Record

**Invariant:** `Bundled provider metadata != independently retrieved provider evidence`.

JANE 239 compared reports with provider metadata in the same bundle. JANE 240 uses a fixed GitHub API origin, a pinned 40-character commit, actual file bytes, Git blob SHA-1, and SHA-256. It will **WITHHOLD** on any missing/mismatching observation. GitHub is one source ancestry, not an independent third witness. A forged local retrieval-metadata file can still fool fixture replay; only the `--live` code path makes the actual HTTPS request.

## Observed provider source

- Source: `DavidWise01/nom/requirements.txt`
- Pinned commit: `e639711f317ea29650df2518a66de7b5eeb9d2c4`
- Git blob SHA-1: `d80d9fc2a3a2b61bfeaee0004be49f7a69cf8f63`
- SHA-256: `4b8183101fd19f071771805a42a31fbb234a7961921fdb8b783a279755a1b5d5`
- GitHub connector independently returned exactly `requests==2.32.3\n`, matching the SHA-1. Local fixture encodes those observed bytes and an explicitly **reconstructed** retrieval record. Do not call its local pass an independent live HTTP run.

## Run

```bash
python -m unittest -v test_provider_check.py
python provider_check.py claim.json --provider provider-response.json --retrieval retrieval-metadata.json --out result.json
# Requires outbound network access; GitHub Actions workflow does this:
python provider_check.py claim.json --live --out live-result.json
```

`--live` uses read-only HTTPS GET on GitHub API at the pinned commit; no arbitrary host is accepted, no secret/token required, and the audit performs no downstream actions. The manual GitHub workflow installs no third-party packages and uploads the receipt. Unverified workflow execution is not a live-result claim.

**Limit:** SHA-1 identifies a Git blob as Git does; SHA-256 independently checks bytes against the pinned claim. This does not prove GitHub infrastructure independence, crawler agency, or Jane's preference. `jane_choice=UNRESOLVED`, `actions_executed=0`.