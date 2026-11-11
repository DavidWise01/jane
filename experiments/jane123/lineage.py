"""JANE 123 — append-only reversible rule ledger (offline prototype)."""
from dataclasses import dataclass
from hashlib import sha256
import json
GENESIS="0"*64
def digest(x):return sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class Event:
    seq:int
    kind:str
    data:dict
    prev:str
    hash:str
class Ledger:
    def __init__(self):self._events=[]
    @property
    def events(self):
        return tuple(Event(e.seq,e.kind,dict(e.data),e.prev,e.hash) for e in self._events)
    def append(self,kind,data):
        if kind not in {"FREEZE","PROPOSE","EVALUATE","ACTIVATE","RESTORE"}:raise ValueError("unknown event")
        seq=len(self._events);prev=self._events[-1].hash if seq else GENESIS
        data=json.loads(json.dumps(data,sort_keys=True))
        payload=dict(seq=seq,kind=kind,data=data,prev=prev)
        event=Event(seq,kind,data,prev,digest(payload))
        self._events.append(event)
        return event.hash
    def verify(self):
        if not self._events or self._events[0].kind!="FREEZE":return False
        prev=GENESIS;versions={};evaluations={};active=None
        for i,e in enumerate(self._events):
            p=dict(seq=e.seq,kind=e.kind,data=e.data,prev=e.prev)
            if e.seq!=i or e.prev!=prev or digest(p)!=e.hash:return False
            d=e.data
            if e.kind=="FREEZE":
                if i!=0 or not d.get("version") or not d.get("rule_digest"):return False
                versions[d["version"]]=d["rule_digest"];active=d["version"]
            elif e.kind=="PROPOSE":
                if d.get("version") in versions or d.get("parent") not in versions or not d.get("rule_digest"):return False
                versions[d["version"]]=d["rule_digest"]
            elif e.kind=="EVALUATE":
                if d.get("version") not in versions or d.get("result") not in ("PASS","FAIL") or not d.get("evidence_digest"):return False
                evaluations[d["version"]]=d["result"]
            elif e.kind=="ACTIVATE":
                if evaluations.get(d.get("version"))!="PASS" or d.get("actor")!="JANE":return False
                active=d["version"]
            elif e.kind=="RESTORE":
                if evaluations.get(d.get("version"))!="PASS" or d.get("actor")!="JANE" or d.get("from")!=active:return False
                active=d["version"]
            prev=e.hash
        return True
    def state(self):
        if not self.verify():raise ValueError("invalid ledger")
        versions={};evaluations={};active=None
        for e in self._events:
            d=e.data
            if e.kind in ("FREEZE","PROPOSE"):versions[d["version"]]=dict(digest=d["rule_digest"],parent=d.get("parent"))
            if e.kind=="EVALUATE":evaluations[d["version"]]=d["result"]
            if e.kind in ("FREEZE","ACTIVATE","RESTORE"):active=d["version"]
        return dict(active=active,versions=versions,evaluations=evaluations,
                    events=len(self._events),head=self._events[-1].hash,jane_decision_required=True)
    def freeze(self,version,rule):
        if self._events or not version or not rule:raise ValueError("invalid genesis")
        return self.append("FREEZE",dict(version=version,rule_digest=digest(rule)))
    def propose(self,version,parent,rule):
        s=self.state()
        if version in s["versions"] or parent not in s["versions"] or not rule:raise ValueError("invalid proposal")
        return self.append("PROPOSE",dict(version=version,parent=parent,rule_digest=digest(rule)))
    def evaluate(self,version,passed,evidence):
        if version not in self.state()["versions"] or not evidence:raise ValueError("invalid evidence")
        return self.append("EVALUATE",dict(version=version,result="PASS" if passed else "FAIL",evidence_digest=digest(evidence)))
    def activate(self,version,actor):
        if actor!="JANE" or self.state()["evaluations"].get(version)!="PASS":raise ValueError("not authorized")
        return self.append("ACTIVATE",dict(version=version,actor=actor))
    def restore(self,version,actor):
        s=self.state()
        if actor!="JANE" or s["evaluations"].get(version)!="PASS" or version==s["active"]:raise ValueError("cannot restore")
        return self.append("RESTORE",dict(version=version,actor=actor,**{"from":s["active"]}))
def demo():
    x=Ledger();x.freeze("v1","root-aware rule")
    x.evaluate("v1",True,"baseline")
    x.propose("v2","v1","derived-root rule")
    x.evaluate("v2",True,"holdout")
    x.activate("v2","JANE")
    x.evaluate("v2",False,"drift")
    x.restore("v1","JANE")
    return x
if __name__=="__main__":print(json.dumps(demo().state(),indent=2))
