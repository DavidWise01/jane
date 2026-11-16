# JANE 252 — The Vote That Could Not Fence the Loser

**Invariant:** Fork resolution does not imply enforced execution exclusivity.

The locally tested demonstration uses two SQLite connections against **one transactional fencing authority**. Host A holds epoch 1 and commits, Host B obtains epoch 2, then A's stale epoch-1 commit is rejected as `FENCED_STALE_EPOCH`. B's epoch-2 commit is accepted. A repeated B operation ID is rejected.

**Local test result:** 31/31 Python unittest cases passed. No external action was executed. Jane's collective choice is `UNRESOLVED`.

**Scope:** This only fences writes in the *same SQLite database*. It does not fence external APIs, GitHub, Railway, or separate independently replicated databases, nor does it authenticate the winning host. SQLite's transaction isolation is the single coordination authority.

The complete executable source, regression tests, demonstrator, detailed offline HTML chapter, and receipt are in the conversation's `jane252-tested.zip`. The GitHub source files and workflow must not be treated as deployed until independently fetched and verified.

**Next:** make the actual destination enforce monotonic epochs atomically. Bind authorization to independently verified JANE 251 resolution receipts and preserve both fork histories.