"""JANE 143 compact receipt verifier. Full 52-test version: downloadable ZIP.
Real Ed25519 checks, fixture registry/anchors, no external attestation.
"""
from dataclasses import dataclass
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from datetime import datetime, timezone, timedelta
import json,re

STAMP="{{ 2026.11.12 }}{{ 11.47.00 }}{{ 123.45.56 }}"
PAT=re.compile(r"^\{\{ (\d{4})\.(\d{2})\.(\d{2}) \}\}\{\{ (\d{2})\.(\d{2})\.(\d{2}) \}\}\{\{ ([+-]?\d{1,3})\.(\d{2})\.(\d{2}) \}\}$")
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def digest(x):return sha256(enc(x)).hexdigest()
def chronos(c,offset):
 m=PAT.fullmatch(c)
 if not m or not -840<=offset<=840:raise ValueError("Chronos")
 v=m.groups();d,am,sec=map(int,v[6:])
 if abs(d)>360 or am>=60 or sec>=60:raise ValueError("angle")
 return datetime(*map(int,v[:6]),tzinfo=timezone(timedelta(minutes=offset))).astimezone(timezone.utc)

@dataclass(frozen=True)
class Case:
 id:str;truth:bool|None;parent:bool;child:bool;weight:int;cohort:str="critical"
 def binding(self):return digest(self.__dict__)
@dataclass(frozen=True)
class Key:
 public:bytes;root:str;active:bool=True
@dataclass(frozen=True)
class Receipt:
 claim:dict;signature:bytes

class FLAY:
 def __init__(self,cases,keys,anchors,now,quorum=3):
  self.cases={c.id:c for c in cases};self.keys=dict(keys);self.anchors=dict(anchors)
  self.now=now;self.quorum=quorum;self.used=set();self.claims={};self.events=[];self.active="frozen_parent"
  if len(self.cases)!=len(tuple(cases)) or not 1<=quorum<=5:raise ValueError("cases/quorum")
  self._event("DECLARE","risk=12,critical=0")
 def _event(self,kind,data):
  e=dict(seq=len(self.events),kind=kind,data=data,prev=self.events[-1]["head"] if self.events else "0"*64)
  e["head"]=digest(e);self.events.append(e)
 def ingest(self,r):
  p=r.claim
  if set(p)!=set(("key_id","case_id","case_digest","truth","nonce","chronos","offset","anchor")):status="SCHEMA"
  else:
   k=self.keys.get(p["key_id"])
   if k is None or not k.active:status="KEY"
   else:
    try:Ed25519PublicKey.from_public_bytes(k.public).verify(r.signature,enc(p));status="SIGNED"
    except (InvalidSignature,ValueError,TypeError):status="SIGNATURE"
    if status=="SIGNED":
     try:
      if abs((self.now-chronos(p["chronos"],p["offset"])).total_seconds())>300:status="STALE"
      elif p["case_id"] not in self.cases or p["case_digest"]!=self.cases[p["case_id"]].binding():status="CASE"
      elif type(p["truth"]) is not bool or len(p["nonce"])<12 or self.anchors.get(k.root)!=p["anchor"]:status="CLAIM"
      elif (k.root,p["nonce"]) in self.used:status="REPLAY"
      else:status="ACCEPTED"
     except (ValueError,TypeError):status="CLAIM"
    if status=="ACCEPTED":
     self.used.add((k.root,p["nonce"]))
     self.claims.setdefault(p["case_id"],[]).append((k.root,p["truth"]))
  self._event("ACCEPT" if status=="ACCEPTED" else "REJECT",dict(status=status,digest=digest(p)))
  return status
 def resolve(self,id):
  pairs=self.claims.get(id,[])
  if len({v for _,v in pairs})>1:return "CONFLICT",None
  if len({root for root,_ in pairs})<self.quorum:return "UNKNOWN",None
  return "RESOLVED",pairs[0][1]
 def evaluate(self):
  parent=[0,0];child=[0,0];delta=[0,0];states={}
  for id,c in sorted(self.cases.items()):
   state,value=self.resolve(id) if c.truth is None else ("ORIGINAL_KNOWN",c.truth)
   states[id]=state;w=c.weight
   if value is None:
    p=[0,w];n=[0,w];d=[-w,w] if c.parent!=c.child else [0,0]
   else:
    p=[w*int(c.parent!=value)]*2;n=[w*int(c.child!=value)]*2;d=[n[0]-p[0]]*2
   for i in (0,1):parent[i]+=p[i];child[i]+=n[i];delta[i]+=d[i]
  status=("QUARANTINE_CONFLICT" if "CONFLICT" in states.values() else
          "HOLD_UNCERTAIN_RISK" if child[1]>0 or child[1]>12 else
          "JANE_REVIEW_CANDIDATE" if delta[1]<0 else "NO_PROVEN_IMPROVEMENT")
  out=dict(version="JANE-143",status=status,parent_risk=parent,child_risk=child,change_interval=delta,case_states=states,active=self.active,learning_applied=False,jane_decision="UNDECIDED")
  self._event("EVALUATE",digest(out))
  return out
