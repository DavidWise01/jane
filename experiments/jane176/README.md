# JANE 176 — The Rules That Change the Verdict

**Natural invariant:** Unchanged evidence does not guarantee unchanged interpretation.

The full Python engine replays one frozen synthetic evidence packet under two explicitly versioned policies, preserves the entire rule set and evidence digests, records both verdicts in a hash-linked local audit trail, and distinguishes policy-induced verdict changes from stable verdicts. It does not activate Jane, validate physical reproduction, or establish independent witnesses.

## Reproducible fixture

- Original 1000; repeated 1003 (difference 3)
- Policy v1 permits difference at most 5 → `DECLARED_FIXTURE_MATCH`
- Policy v2 permits difference at most 2 → `REJECTED`
- Both verdicts reference the **identical evidence digest**

Run `python -m unittest -v test_policy.py` (45 tests), then `python policy.py` for `result.json`.

A valid local hash chain cannot detect clean suffix truncation unless the final head is retained externally. This is a local demonstration, not a deployed evidence service.

## Natural bound 177 — Policy authority

A correctly versioned rule can still be unauthorized. Preserve who approved each policy, the scope and effective time, and whether it was allowed to change the verdict; never confuse a policy replay with authorized policy activation.