"""JANE 136 — signed checkpoint comparator (offline fixtures, not deployed witnesses)."""
from dataclasses import dataclass
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
import json

GENESIS="0"*64
def encode(x):return json.dumps(x,sort_keys=True,separators=(",",":")).encode()
def digest(x):return sha256(encode(x)).hexdigest()
def append(events,text):
    events=tuple(events);n=len(events);prev=events[-1]["head"] if n else GENESIS
    return events+({"index":n,"text":text,"prev":prev,
                    "head":digest(dict(index=n,text=text,prev=prev))},)
def chain_valid(events):
    prev=GENESIS
    for n,e in enumerate(events):
        if e["index"]!=n or e["prev"]!=prev or e["head"]!=digest(dict(index=n,text=e["text"],prev=prev)):
            return False
        prev=e["head"]
    return True
@dataclass(frozen=True)
class Custodian:
    root:str
    public_key:bytes
@dataclass(frozen=True)
class Receipt:
    payload:dict
    signature:bytes
def verify(events,receipts,keys,quorum=3):
    events=tuple(events);receipts=tuple(receipts)
    if len(events)>1024 or len(receipts)>32 or quorum<1:raise ValueError("budget")
    if not chain_valid(events):return dict(status="CHAIN_TAMPERED",learning_applied=False)
    local=(len(events)-1,events[-1]["head"] if events else GENESIS)
    roots={};errors=[]
    for r in receipts:
        p=r.payload;k=keys.get(p.get("key_id"))
        if not k or set(p)!={"domain","key_id","nonce","sequence","head","chronos"} or p["domain"]!="JANE-136":
            errors.append("BAD_SCHEMA_OR_KEY");continue
        try:Ed25519PublicKey.from_public_bytes(k.public_key).verify(r.signature,encode(p))
        except (InvalidSignature,ValueError,TypeError):
            errors.append("BAD_SIGNATURE");continue
        pair=(p["sequence"],p["head"])
        if k.root in roots and roots[k.root]!=pair:
            errors.append("ROOT_CONFLICT");continue
        roots[k.root]=pair
    counts={}
    for pair in roots.values():counts[pair]=counts.get(pair,0)+1
    anchor=max(counts,key=counts.get) if counts else None
    agreeing=counts.get(anchor,0)
    status=("ROOT_CONFLICT" if "ROOT_CONFLICT" in errors else
            "INSUFFICIENT_ROOTS" if agreeing<quorum else
            "ROLLBACK_DETECTED" if anchor[0]>local[0] else
            "FORK_DETECTED" if anchor[0]==local[0] and anchor[1]!=local[1] else
            "ANCHORED_MATCH" if anchor==local else "LOCAL_AHEAD")
    return dict(status=status,local_sequence=local[0],anchor_sequence=anchor[0] if anchor else None,
                agreeing_roots=agreeing,errors=errors,learning_applied=False,
                jane_decision="UNDECIDED",caveat="Keys and custody roots are local fixtures; no external custody verified.")
