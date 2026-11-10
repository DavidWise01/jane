"""JANE 117: bounded fixture-driven scout; no autonomous network calls or learning."""
from dataclasses import dataclass
from hashlib import sha256
import json

MAX_BUDGET=6
@dataclass(frozen=True)
class Case:
    name: str
    urls: tuple
    roots: tuple
    independent: bool

@dataclass(frozen=True)
class Finding:
    name: str
    question: str
    distinction: str
    url: str
    origin: str
    excerpt: str
    cases: tuple

CATALOG=(
    Finding("source_ancestry","Can separate URLs share one origin?",
            "compare root ancestry, not URL count",
            "https://www.w3.org/TR/prov-o/","W3C:PROV-O",
            "Entities can be connected by derivation relationships.",
            (Case("mirror",("github","0root"),("owned","owned"),False),
             Case("syndication",("site1","site2"),("wire","wire"),False),
             Case("independent",("site3","site4"),("a","b"),True))),
    Finding("word_count","Does longer text establish independence?",
            "prefer longer claims","https://example.org/length","demo",
            "Length is not proof of independence.",
            (Case("copy",("a","b"),("same","same"),False),))
)
HOLDOUT=(
    Case("transitive_copy",("a","b","c"),("wire","wire","wire"),False),
    Case("two_originals",("d","e"),("author-a","author-b"),True),
    Case("second_mirror",("github2","0root2"),("owned","owned"),False),
    Case("unknown_root",("f","g"),("known",None),False),
)
def old_rule(c):
    return len(set(c.urls))>=2
def lineage_rule(c):
    return None if None in c.roots else len(set(c.roots))>=2
def discover(catalog=CATALOG,holdout=HOLDOUT,budget=MAX_BUDGET):
    if not 0<budget<=MAX_BUDGET: raise ValueError("invalid budget")
    examined=[]
    candidate=None
    for finding in catalog[:budget]:
        errors=sum(old_rule(c)!=c.independent for c in finding.cases)
        examined.append({"finding":finding.name,"old_rule_errors":errors})
        if finding.name=="source_ancestry" and errors:
            candidate=finding
            break
    if candidate is None:
        return {"status":"NO_DISCOVERY","examined":examined,"learning_applied":False}
    known=[c for c in holdout if None not in c.roots]
    old=sum(old_rule(c)==c.independent for c in known)
    new=sum(lineage_rule(c)==c.independent for c in known)
    abstain=sum(lineage_rule(c) is None for c in holdout)
    improved=new>old and abstain>=1
    packet={
        "version":"JANE-117","kind":"DISCOVERY_CANDIDATE",
        "scout_choice":candidate.question,"candidate":candidate.distinction,
        "source":{"url":candidate.url,"origin":candidate.origin,
                  "excerpt":candidate.excerpt,"trust":"UNTRUSTED_DATA"},
        "exploration":examined,
        "holdout":{"cases":len(holdout),"known_cases":len(known),
                   "old_correct":old,"revised_correct":new,"abstentions":abstain},
        "status":"JANE_REVIEW_REQUIRED" if improved else "FLAY_MORE_EVIDENCE",
        "learning_applied":False,"jane_decision":"UNDECIDED",
        "limitations":["Synthetic fixtures, not live internet discovery",
                       "Origin labels supplied, not independently verified",
                       "Distinct roots are a simplified independence model"]
    }
    packet["sha256"]=sha256(json.dumps(packet,sort_keys=True).encode()).hexdigest()
    return packet
if __name__=="__main__":
    print(json.dumps(discover(),indent=2))
