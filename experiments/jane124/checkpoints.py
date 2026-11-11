"""JANE 124 — offline three-witness checkpoint verification.
Witness identity and ancestry are declared inputs, NOT cryptographic attestations.
"""
from dataclasses import dataclass
from hashlib import sha256
import json

ZERO="0"*64
def hash_of(x):return sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class Event:
    seq:int
    text:str
    prev:str
    hash:str
def append(events,text):
    prev=events[-1].hash if events else ZERO
    seq=len(events)
    return tuple(events)+(Event(seq,text,prev,hash_of(dict(seq=seq,text=text,prev=prev))),)
def chain_valid(events):
    prev=ZERO
    for i,e in enumerate(events):
        if (i,e.prev,e.hash)!=(e.seq,prev,hash_of(dict(seq=e.seq,text=e.text,prev=e.prev))):return False
        prev=e.hash
    return True
@dataclass(frozen=True)
class Witness:
    id:str
    ancestry:str|None
    seq:int
    head:str
    surface:str="external"
def ancestry(w):
    return "owned:canonical" if w.surface in ("github","0root.ai") else w.ancestry
def verify(events,witnesses):
    events=tuple(events);witnesses=tuple(witnesses)
    if len(events)>4096 or len(witnesses)>16:raise ValueError("bounded evidence")
    if not chain_valid(events):return {"status":"CHAIN_TAMPERED","learning_applied":False}
    local=(len(events)-1,events[-1].hash if events else ZERO)
    seen=set();roots={};conflict=False
    for w in witnesses:
        if w.id in seen or not w.id or w.seq < -1 or len(w.head)!=64 or any(c not in "0123456789abcdef" for c in w.head):conflict=True;continue
        seen.add(w.id)
        a=ancestry(w)
        if not a:continue
        key=(w.seq,w.head)
        if a in roots and roots[a]!=key:conflict=True
        roots[a]=key
    match=sum(v==local for v in roots.values())
    ahead=any(v[0]>local[0] for v in roots.values())
    fork=any(v[0]==local[0] and v[1]!=local[1] for v in roots.values())
    state=("WITNESS_CONFLICT" if conflict else "TRUNCATION_SUSPECTED" if ahead else
           "FORK_OR_TAMPER_SUSPECTED" if fork else "THREE_WITNESS_MATCH" if match>=3 else
           "INSUFFICIENT_INDEPENDENT_WITNESSES")
    result=dict(version="JANE-124",status=state,local_seq=local[0],local_head=local[1],
                independent_matches=match,declared_ancestries=len(roots),
                learning_applied=False,jane_decision="UNDECIDED",
                limitation="Witness ancestry and custody unverified; no cryptographic authentication.")
    result["audit_digest"]=hash_of(result)
    return result
def demo():
    e=()
    for x in ("freeze","pass","propose","activate","fail","restore"):e=append(e,x)
    h=e[-1].hash
    w=(Witness("owned","owned",5,h,"github"),Witness("external-A","A",5,h),
       Witness("external-B","B",5,h))
    return {"intact":verify(e,w),"truncated":verify(e[:-2],w),
            "mirrors":verify(e,(Witness("git","owned",5,h,"github"),
                                 Witness("site","owned",5,h,"0root.ai"),
                                 Witness("external-A","A",5,h)))}
if __name__=="__main__":print(json.dumps(demo(),indent=2))
