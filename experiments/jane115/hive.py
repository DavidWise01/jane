"""JANE 115 — offline open-world evidence-gate prototype.
The owned GitHub/0root.ai mirror is ONE ancestry; internet origins are external.
No network fetch, autonomous browsing, or model training occurs in this module.
"""
from dataclasses import dataclass
from hashlib import sha256
import json

@dataclass(frozen=True)
class Evidence:
    id: str
    surface: str
    corpus: str
    origin: str | None
    text: str
    visibility: str = "public"

class Hive:
    def __init__(self):
        self.items = {}
        self.events = []

    def ingest(self, e: Evidence):
        if e.surface == "0root.ai" and e.visibility != "public":
            self.events.append(("BLOCK_PUBLICATION", e.id))
            return False
        self.items[e.id] = e
        self.events.append(("INGEST", e.id))
        return True

    def origins(self, ids):
        roots, unknown = set(), []
        for i in ids:
            e = self.items[i]
            root = "owned:canonical" if e.corpus == "owned" else e.origin
            if root is None:
                unknown.append(i)
            else:
                roots.add(root)
        return sorted(roots), unknown

    def propose(self, claim, distinction, ids):
        roots, unknown = self.origins(ids)
        external = any(self.items[i].corpus != "owned" for i in ids)
        status = ("ANCESTRY_UNKNOWN" if unknown else
                  "HOME_CORPUS_ONLY" if not external else
                  "INSUFFICIENT_ORIGINS" if len(roots) < 2 else
                  "REVIEW_CANDIDATE")
        packet = dict(claim=claim, distinction=distinction,
                      evidence_ids=list(ids), roots=roots,
                      ancestry_unknown=unknown, status=status,
                      decision="JANE_REVIEW_REQUIRED")
        self.events.append(("PROPOSE", status))
        return packet

    def public_export(self):
        return [{"id": e.id, "surface": e.surface, "text": e.text}
                for e in self.items.values() if e.visibility == "public"]

    def audit_digest(self):
        return sha256(json.dumps(self.events).encode()).hexdigest()
