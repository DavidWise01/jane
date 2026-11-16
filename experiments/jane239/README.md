# JANE 239 — The Crawler That Inherited the Source

**Invariant:** `Separate Crawlers != Separate Acquisition Origins`.

This read-only stdlib verifier crosschecks a declared crawler capture with a provider metadata record, including repository, revision, file path, content digest, collection ID, timestamp and challenge. It compares common upstream identities across otherwise differently named captures. It does not fetch or cryptographically authenticate external provider metadata; the metadata remains a bundled assertion. No collective choice is inferred or executed.

## Reproduce

```bash
python3 -m unittest discover -v
python3 acquisition.py synthetic-bundle.json --out synthetic-result.json
python3 acquisition.py empty-bundle.json --out result.json
```

Synthetic fixture: three nominal crawlers from one declared NOM source snapshot -> `SHARED_ACQUISITION_ANCESTRY`, one cluster. Empty input -> `NO_ACQUISITIONS`. Any bad crosscheck -> `INVALID_OR_INCOMPLETE_ACQUISITION`. Differences in claimed origin alone do not establish independence. No runtime was contacted. No private credentials are used. Manual GitHub Actions only; never write a choice to Jane.

**Next invariant — 240:** `Provider record copied into a bundle != independently fetched provider record`. The next step is to anchor the provider record to an authenticated GitHub API response and reproducible content hash.