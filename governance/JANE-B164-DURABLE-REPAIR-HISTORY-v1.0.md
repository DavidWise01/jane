# B164 — Durable Repair Lifecycle, Cooldown and Owner Reset

Natural invariant: **repair attempts are historical events, not disposable retry counters.** B163 recorded a per-run evidence snapshot; B164 reconstructs a versioned repair history from GitHub's existing **open and closed** FORMIC pull requests. It does not edit the source repositories or create new PRs.

## Lifecycle

```
NO PREVIOUS PR -> NO_PREVIOUS_PROPOSAL (not autonomous permission)
OPEN PR        -> HOLD_EXISTING_OPEN_PR
CLOSED <30d    -> HOLD_COOLDOWN
CLOSED >=30d   -> COOLDOWN_ELAPSED_OWNER_RESET_REQUIRED
MERGED BY OWNER -> ALREADY_APPLIED_OBSERVE_ONLY
MISSING HISTORY -> HOLD_PR_HISTORY_UNAVAILABLE
TRUNCATED HISTORY -> HOLD_HISTORY_TRUNCATED

Every state retains: reusableConsent=false; noAutomaticRetry=true.
```

The cooldown starts at the closing timestamp. The clock is an explicit input to the pure reference calculation and the work is re-derived each run. An elapsed cooldown is **not** authorization to reattempt a repair. A fresh repository-owner policy decision and a future separately designed, reviewable versioned repair branch are required; existing B161 retains its more conservative closed-PR suppression.

## Source provenance

- GitHub PR timeline and PR number are the durable upstream record.
- Each bounded read-only run emits sorted per-repository evidence into an SHA-256 chained JSON artifact.
- GitHub Actions artifacts have a retention window (configured 30 days); this isn't permanent shared storage, and snapshot chains aren't signed attestation.
- History truncation, unrecognized timelines, inaccessible API data and unknown authority always HOLD.
- The agent does not interpret green CI as proof of benefit and never creates or merges PRs here.

## Ecosphere preservation

a/H/a1 = source provenance; b/O/b1 = health observation; c/N/c1 = improvement reasoning; d = derived read-only evidence view. There are 3 original witnesses, 1 observation layer, no quorum, and zero defined ISA instructions. The 366 symbolic addresses are not 366 GitHub repositories.

## Next bound

B165: owner-authenticated revision of repair policy with strict audit evidence and explicit versioned change intent, rather than granting implicit retry authority from a timer.
