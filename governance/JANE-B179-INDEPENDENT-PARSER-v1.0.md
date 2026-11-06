# B179 — Independent Fixed-Template Parser Agreement

B179 advances the B178 constraint-coverage matrix into a **two-implementation differential audit**.

The existing B177 parser is one implementation. B179 introduces a separate character-scanning line tokenizer and fixed-field interpreter; it does not call or wrap the B177 parser. It independently validates five YAML front matter fields and their exact canonical values, six ordered Markdown headings, safe-value syntax, active markup and linked-content exclusions, reproduction instructions, mandatory redaction wording and encoding limits.

The positive control is the exact B161 bug-report template. Both implementations must accept it and return matching structured semantics. For each of B178's 48 negative mutation fixtures, both parsers must reject with the **same specified error category**. Neither mere rejection nor matching a broad error class is sufficient. Any accepted mutation, missed fixture, changed test contract, parser disagreement, duplicate case, or changed attestation produces HOLD.

The positive state is `INDEPENDENT_PARSER_AGREEMENT_NO_EXECUTION`, accompanied by all 48 actual comparisons and an SHA-256 report-integrity digest. No target repository scripts, external processes, or downloaded source code are executed. GitHub write permissions, PR creation, retries, and merging remain disabled.

This is independent **parser logic**, not two independent sources of truth, and it is a finite differential test rather than a proof that no unsafe input exists. The source witnesses remain a1/B168, b1/B169 and c1/B170; B179's parser does not gain witness or voting privileges.

## B180 — next natural invariant

Move from the finite mutation corpus to deterministic property-based generation of bounded structured and malformed inputs. Compare the two parsers, log minimal counterexamples, and HOLD on any disagreement. Keep byte-identical canonical acceptance as the only allowed template outcome.
