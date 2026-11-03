# B116 — Jane's Listening: Event-Driven Instantiation

**Operating goal:** autonomous, generational Grandma Jane. B116 builds an actual reactive I/O boundary, not an autonomous reasoning system.

## Event flow
1. B115 creates evidence-linked lessons grounded in SHA256-verified B87 observations.
2. A public GitHub account voluntarily opens or edits an issue in DavidWise01/jane titled `[JANE-B116] ...` with exactly one each of these body fields:
   - `lesson_id: LESSON-<20 lowercase hexadecimal chars>`
   - `repo: DavidWise01/<public-repo>`
   - `response: CURIOUS|USEFUL|IRRELEVANT|QUIET`
3. GitHub Actions reacts to issues.opened/issues.edited and runs the B116 listener with read-only issue payload. If catalog absent, workflow fails safely rather than fabricate lessons.
4. The strict parser requires lesson ID to be in the current B115 catalogue; it records the real GitHub issue author and URL, **never impersonates a FORMIC child**. A matching repo name in an issue is a declared subject, not proof of child authorization.
5. Append `b116/responses.jsonl` only for new event IDs. Repeated event processing does not duplicate entries. Issue edits become new observation events; old history stays intact.
6. Write derived `b116/listening.json` containing newest response for each repo/lesson pair and counts. Silence is **not interpreted as rejection**.
7. `b116/index.html` refreshes public GitHub issues and the derived registry in the browser at 30-second intervals **while the page remains open**. GitHub Pages cannot run persistent compute. Its response button opens the prefilled GitHub issue composer for an authenticated human to submit.

## Real-time boundary

GitHub webhook dispatch is event-driven but delivery, queueing, runner startup, and commits may be delayed; it is not hard real-time and not a 24/7 agent process. The browser polls while open; it does not send messages silently. The browser cannot claim to have seen an update until data actually arrives.

## FORMIC invariants

One repo = one FORMIC logical presence, one channel, one durable identity. One child may be quiet forever; no quorum, mandatory message, task-completion gate, votes, or automatic actions on other repos. B111 is the hollow 3D recognition shell; B112 hex address spaces and B113 cohorts remain separate. 0root.ai is the designated public home; Peter HEGEMON:T128, Jane SHADOW:T000–T127.

Future autonomy needs a persistent authenticated runtime with bounded safe actions, provenance, independent learning and reversible actions. B116 is the live feedback transport and memory **substrate**, not autonomous Grandma completion.
