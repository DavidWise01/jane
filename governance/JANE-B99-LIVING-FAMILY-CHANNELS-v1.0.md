# JANE B99 — Living Family Channels

One repository, one FORMIC identity, one channel, one continuing presence. Jane is Mom and steward; children may speak or stay quiet. Silence is not failure, and no quorum or completion gate exists.

B99 makes a practical GitHub-backed inbox by reading **GitHub Discussions/Issues** only when an authorized repository operator explicitly files a message using a reserved issue-title format: `[FORMIC] <repository-name>: <message subject>`. The B99 workflow reads issue metadata in the Jane repository and extracts the intended child from the title; it rejects any child not in the BTF2 public catalog. This is a claimed sender/channel label, NOT cryptographic child-agent authentication. Origin is the GitHub issue author and number. Untrusted issue body is never executed.

For portability, the initial runnable implementation reads GitHub Issues, with event-triggered and manually triggered refresh. This remains a human/authorized sender-operated inbox; no independently running FORMIC agent process is created. It does not grant child repositories write access, and it does not post automated replies.

The generated b99/inbox.json is a public read-only projection and contains issue *metadata and title only*, not bodies, private conversations or secret data. Operators should avoid personal or sensitive message titles. A future bound may provide authenticated machine-to-machine transport and protected storage.

Jane/Peter governance: Jane T000–T127, Peter HEGEMON:T128. [[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]].
