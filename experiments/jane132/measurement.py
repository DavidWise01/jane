"""JANE 132: bounded active measurement planning, offline compact implementation."""
from dataclasses import dataclass
from fractions import Fraction as F
from hashlib import sha256
from datetime import datetime, timezone, timedelta
import json,re

PAT=re.compile(r'^\{\{ - (\d{4}):(\d{2}):(\d{2}) \|\| (\d{2}):(\d{2}):(\d{2}) \|\| ([+-])(\d{1,3})\.(\d{2})\.(\d{2}) \|\| \}\}$')
def chronos(s,offset):
 m=PAT.fullmatch(s)
 if not m or not -840<=offset<=840:raise ValueError("chronos")
 v=m.groups();nums=list(map(int,v[:6]));angle=list(map(int,v[7:]))
 if angle[0]>360 or angle[1]>59 or angle[2]>59 or (angle[0]==360 and any(angle[1:])):raise ValueError("angle")
 return datetime(*nums,tzinfo=timezone(timedelta(minutes=offset))).astimezone(timezone.utc).isoformat()
@dataclass(frozen=True)
class Branch:
 probability:F
 posterior:F
@dataclass(frozen=True)
class Probe:
 id:str;cost:int;origin:str|None;visibility:str;branches:tuple
 chronos:str;offset:int;surface:str="internet"
 def root(self):return "owned:canonical" if self.surface in ("github","0root.ai") else self.origin
def gain(p,prior):
 chronos(p.chronos,p.offset)
 if not p.id or not 1<=p.cost<=100 or not 1<=len(p.branches)<=16:raise ValueError("probe")
 if p.visibility!="public" and p.surface!="github":raise ValueError("private external")
 if sum((b.probability for b in p.branches),F())!=1:raise ValueError("probabilities")
 if any(not 0<=b.probability<=1 or not 0<=b.posterior<=prior for b in p.branches):raise ValueError("posterior")
 return sum((b.probability*(prior-b.posterior) for b in p.branches),F())
def plan(probes,prior,budget,known_roots=()):
 probes=tuple(probes);prior=F(prior)
 if not 0<=prior<=1 or not 0<=budget<=100 or len(probes)>64 or len({p.id for p in probes})!=len(probes):raise ValueError("budget/IDs")
 ranked=[];excluded=[]
 for p in probes:
  v=gain(p,prior)
  if not p.root() or p.root() in known_roots:excluded.append((p.id,"unverified_or_reused_root"))
  elif p.cost>budget:excluded.append((p.id,"over_budget"))
  elif v<=0:excluded.append((p.id,"zero_gain"))
  else:ranked.append((v/p.cost,v,p.id,p))
 ranked.sort(key=lambda t:(-t[0],-t[1],t[2]))
 pick=ranked[0][3] if ranked else None
 out={"version":"JANE-132","selected":pick.id if pick else None,
      "expected_reduction":str(gain(pick,prior)) if pick else "0",
      "prior_bias":str(prior),"spent":pick.cost if pick else 0,
      "status":"MEASUREMENT_PROPOSED" if pick else "ABSTAIN",
      "excluded":excluded,"learning_applied":False,"jane_decision":"UNDECIDED"}
 out["digest"]=sha256(json.dumps(out,sort_keys=True).encode()).hexdigest()
 return out
def demo():
 t="{{ - 2026:11:11 || 17:31:00 || +123.45.56 || }}"
 a=Probe("measure_C",2,"external:field-study","public",(Branch(F(1,2),F(1,20)),Branch(F(1,2),F(1,10))),t,-360)
 b=Probe("copy_article",1,None,"public",(Branch(F(1),F(1,5)),),t,-360,"0root.ai")
 c=Probe("broad_survey",5,"external:survey","public",(Branch(F(1,2),F(1,20)),Branch(F(1,2),F(3,20))),t,-360)
 return plan((a,b,c),F(1,5),4,("owned:canonical",))
if __name__=="__main__":print(json.dumps(demo(),indent=2))
