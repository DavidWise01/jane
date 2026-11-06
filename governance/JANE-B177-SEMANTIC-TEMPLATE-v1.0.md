# B177 — Semantic Validation of the Fixed Issue Template

B176 compared two independently implemented file-inventory algorithms. B177 advances the boundary from *files are identical* to *the only added file has the expected safe structure and purpose*, while keeping the analysis strictly data-only.

The only accepted change is the exact canonical B161 bug-report template at `.github/ISSUE_TEMPLATE/bug_report.md`. Its allowed YAML front matter is the five fixed keys `name`, `about`, `title`, `labels`, and `assignees`, each appearing once with its canonical value. The validator rejects duplicate or unfamiliar keys, disallowed YAML special syntax, dynamic interpolations, CRLF/BOM and oversized text. Its Markdown headings must appear in the exact expected order, the three reproduction prompts and personal-information removal warning must appear, and HTML/script-like or reference-link patterns are rejected. Finally, the complete file must equal the canonical B161 template and SHA-256 value from the audited B168 proposal.

B177 requires **B168 proof integrity** and a **matching B176 differential tree attestation** over the same repository, proposal digest, base commit and one approved added path. A passing B177 record is `SEMANTICALLY_VALID_FIXED_TEMPLATE_NO_EXECUTION`. Invalid/expired upstream evidence, tampered template, unexpected fields, noncanonical content, missing proof or any failed required check produces HOLD.

The bounded scanner reads up to eight existing committed proof files and uses B176's live read-only workflow to reconstruct the source evidence. It never downloads or runs arbitrary repository scripts, creates PRs, retries, merges or writes to another GitHub repository.

Semantic safety is not a general theorem about arbitrary Markdown or YAML content. The positive result means *this exact known fixed template* passed this specific allowlist. Neither GitHub CI for the proposed change nor human owner authorization is established.

Canonical witnesses: a1/B168, b1/B169 and c1/B170. B176/B177 are derived read-only observations, not votes or new witnesses. One observer layer; no quorum; zero defined ISA instructions.

## B178 natural bound

Build a constraint-completeness audit that proves every field, heading and prohibited-content rule has both an accepted and rejected regression fixture, with no hidden coercion or invented authority.
