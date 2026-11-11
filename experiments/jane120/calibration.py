"""JANE 120 — measured information gain; offline deterministic experiment."""
from dataclasses import dataclass
from fractions import Fraction as F
from hashlib import sha256
import json

@dataclass(frozen=True)
class Trial:
    scout: str
    predicted: F
    before: int
    after: int
    total: int
    lineage: str
    visibility: str = "public"

def evaluate(rows):
    rows=tuple(rows)
    if len(rows)>128: raise ValueError("budget")
    keys=set()
    groups={}
    for t in rows:
        if (not t.scout or not t.lineage or t.visibility!="public" or not 0<=t.predicted<=1
            or not 0<=t.before<=t.total or not 0<=t.after<=t.total or t.total<1):
            raise ValueError("invalid evidence")
        key=(t.scout,t.lineage)
        if key in keys: raise ValueError("duplicate lineage")
        keys.add(key)
        groups.setdefault(t.scout,[]).append(t)
    result={}
    for name,items in sorted(groups.items()):
        n=len(items)
        result[name]={"trials":n,
          "predicted":str(sum((t.predicted for t in items),F())/n),
          "observed":str(F(sum(t.after>t.before for t in items),n)),
          "brier":str(sum(((t.predicted-int(t.after>t.before))**2 for t in items),F())/n),
          "accuracy_delta":str(sum((F(t.after-t.before,t.total) for t in items),F())/n)}
    p={"version":"JANE-120","results":result,"learning_applied":False,"jane_decision":"UNDECIDED"}
    p["digest"]=sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()
    return p

def route(packet,min_trials=2):
    eligible=[(F(v["brier"]),name) for name,v in packet["results"].items()
              if v["trials"]>=min_trials and F(v["accuracy_delta"])>0]
    return {"proposal":min(eligible)[1] if eligible else None,
            "status":"JANE_REVIEW" if eligible else "ABSTAIN","learning_applied":False}
