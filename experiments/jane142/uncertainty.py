"""JANE 142: compact missing-outcome risk bounds, offline fixtures."""
from dataclasses import dataclass
from hashlib import sha256
from fractions import Fraction
import json
CHRONOS="{{ 2026.11.12 }}{{ 09.51.00 }}{{ 123.45.56 }}"
def digest(x):return sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
@dataclass(frozen=True)
class Case:
 id:str;cohort:str;truth:bool|None;parent:bool;child:bool;severity:int;reversibility:int;origin:str;content_hash:str
@dataclass(frozen=True)
class Budget:
 overall:int;cohorts:tuple;max_new_severe:int=0
 def __post_init__(self):
  if self.overall<0 or self.max_new_severe<0 or len({k for k,v in self.cohorts})!=len(self.cohorts) or any(not k or v<0 for k,v in self.cohorts):raise ValueError('budget')
@dataclass(frozen=True)
class Probe:
 case_id:str;cost:int;root:str;potentially_verifiable:bool
class Flay:
 def __init__(self,budget):
  self.budget=budget;self.active="frozen_parent";self.events=[]
  self._event("DECLARE_BUDGET",str(budget))
 def _event(self,kind,detail):
  event=dict(seq=len(self.events),kind=kind,detail=detail,prev=self.events[-1]['head'] if self.events else '0'*64)
  event['head']=digest(event);self.events.append(event)
 def evaluate(self,cases,probes=(),training_hashes=(),probe_budget=4):
  cases=tuple(cases);probes=tuple(probes)
  if not 1<=len(cases)<=256 or not 0<=probe_budget<=100 or len({c.id for c in cases})!=len(cases):raise ValueError('case budget/duplicates')
  for c in cases:
   if not c.id or not c.cohort or not c.origin or type(c.parent)is not bool or type(c.child)is not bool or c.truth is not None and type(c.truth)is not bool or not 1<=c.severity<=10 or not 1<=c.reversibility<=5 or len(c.content_hash)!=64:raise ValueError('case')
  if any(c.content_hash in training_hashes for c in cases):
   self._event("QUARANTINE","HOLDOUT_LEAKAGE")
   return dict(status="HOLDOUT_LEAKAGE",learning_applied=False,jane_decision="UNDECIDED")
  limits=dict(self.budget.cohorts)
  if {c.cohort for c in cases}!=set(limits):return dict(status="UNDECLARED_COHORT",learning_applied=False,jane_decision="UNDECIDED")
  parent=[0,0];child=[0,0];delta=[0,0];unknown={};cohorts=[];new_severe=0
  for cohort in sorted(limits):
   group=[c for c in cases if c.cohort==cohort]
   if len(group)<2:return dict(status="INSUFFICIENT_COHORT",learning_applied=False,jane_decision="UNDECIDED")
   pl=ph=cl=ch=dl=dh=0
   for c in group:
    w=c.severity*c.reversibility
    if c.truth is None:
     unknown[c.id]=c
     ph+=w;ch+=w
     if c.parent!=c.child:dl-=w;dh+=w
    else:
     p=w if c.parent!=c.truth else 0
     n=w if c.child!=c.truth else 0
     pl+=p;ph+=p;cl+=n;ch+=n;dl+=n-p;dh+=n-p
     new_severe+=int(c.severity>=8 and p==0 and n>0)
   parent[0]+=pl;parent[1]+=ph;child[0]+=cl;child[1]+=ch;delta[0]+=dl;delta[1]+=dh
   cohorts.append(dict(cohort=cohort,parent=[pl,ph],child=[cl,ch],change=[dl,dh],ceiling=limits[cohort],unknown=sum(c.truth is None for c in group)))
  if new_severe>self.budget.max_new_severe:status="BLOCK_KNOWN_SEVERE_ERROR"
  elif child[0]>self.budget.overall or any(x['child'][0]>x['ceiling'] for x in cohorts):status="BLOCK_CERTAIN_EXCESS_RISK"
  elif child[1]>self.budget.overall or any(x['child'][1]>x['ceiling'] for x in cohorts):status="HOLD_UNCERTAIN_RISK"
  elif delta[1]<0:status="JANE_REVIEW_CANDIDATE"
  else:status="NO_PROVEN_RISK_IMPROVEMENT"
  eligible=[]
  for p in probes:
   if p.case_id in unknown and 1<=p.cost<=probe_budget and p.root and p.potentially_verifiable:
    w=unknown[p.case_id].severity*unknown[p.case_id].reversibility
    eligible.append((Fraction(w,p.cost),w,p.case_id))
  eligible.sort(key=lambda x:(-x[0],-x[1],x[2]))
  result=dict(version="JANE-142",chronos=CHRONOS,status=status,parent_risk=parent,child_risk=child,change_interval=delta,unknown_count=len(unknown),cohorts=cohorts,next_probe=eligible[0][2] if eligible else None,probe_score=str(eligible[0][0]) if eligible else None,active=self.active,probe_executed=False,learning_applied=False,jane_decision="UNDECIDED")
  result["digest"]=digest(result);self._event("BOUND_RISK",result["digest"])
  return result
 def audit(self):
  prev='0'*64
  for i,e in enumerate(self.events):
   if e['seq']!=i or e['prev']!=prev or e['head']!=digest({k:v for k,v in e.items() if k!='head'}):return 'TAMPERED'
   prev=e['head']
  return 'VALID_LOCAL_CHAIN'
def demo():
 b=Budget(12,(('routine',12),('critical',0)))
 cases=[Case(f'R{i}','routine',True,False,True,2,1,'external:r',f'{i+1:064x}') for i in range(6)]
 cases +=[Case(f'C{i}','critical',None,True,False,10,5,'external:c',f'{i+50:064x}') for i in range(2)]
 f=Flay(b);r=f.evaluate(cases,(Probe('C0',2,'scout:external',True),Probe('C1',5,'scout:external',True)))
 return f,r
if __name__=='__main__':print(json.dumps(demo()[1],indent=2))
