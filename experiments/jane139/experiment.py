"""JANE 139: compact recursive hypothesis comparison, review only."""
from dataclasses import dataclass
from hashlib import sha256
import json
ANCHORS=("upperleftrear","centerrear","lowerleftrear","centerupper","center","centerlower","upperrightfront","rightcenter","lowerrightfront")
CHRONOS="{{ 2026.11.12 }}{{ 08.49.00 }}{{ 123.45.56 }}"
def digest(x):return sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
@dataclass(frozen=True)
class Cell:
 path:tuple
 parent:str|None
 root:str
 chronos:str
 rule:str
 hash:str
class Experiment:
 def __init__(self,root="owned:canonical"):
  self.cells={};self.events=[];self.active=()
  self._create((),None,root,CHRONOS,"count_urls")
 def _event(self,kind,data):
  e=dict(seq=len(self.events),kind=kind,data=data,prev=self.events[-1]["head"] if self.events else "0"*64)
  e["head"]=digest(e);self.events.append(e)
 def _create(self,path,parent,root,chronos,rule):
  body=dict(path=path,parent=parent,root=root,chronos=chronos,rule=rule)
  c=Cell(path,parent,root,chronos,rule,digest(body));self.cells[path]=c
  self._event("FREEZE" if not path else "PROPOSE",dict(path=path,hash=c.hash))
  return c
 def propose(self,path,anchor,rule):
  if path not in self.cells or anchor not in ANCHORS or rule not in ("count_urls","root_aware","always_yes"):raise ValueError("invalid")
  child=path+(anchor,)
  if child in self.cells or len(child)>8 or len(self.cells)>=729:raise ValueError("bound")
  p=self.cells[path]
  return self._create(child,p.hash,p.root,p.chronos,rule)
 @staticmethod
 def predict(rule,urls,roots):
  if rule=="count_urls":return len(set(urls))>=2
  if rule=="root_aware":return None if None in roots else len(set(roots))>=2
  if rule=="always_yes":return True
  raise ValueError("rule")
 def compare(self,base,new,cases):
  if base==new or base not in self.cells or new not in self.cells:raise ValueError("branches")
  cases=tuple(cases)
  if not 1<=len(cases)<=128 or len({c[0] for c in cases})!=len(cases):raise ValueError("cases")
  gains=regressions=bcorrect=ncorrect=abstain=0;groups=set()
  for case_id,split,urls,roots,truth,ancestry in cases:
   if split!="holdout" or not ancestry or len(urls)!=len(roots) or not urls or truth is None:raise ValueError("case")
   groups.add(ancestry)
   a=self.predict(self.cells[base].rule,urls,roots)
   b=self.predict(self.cells[new].rule,urls,roots)
   ac=a is not None and a==truth;bc=b is not None and b==truth
   bcorrect+=ac;ncorrect+=bc;gains+=int(not ac and bc);regressions+=int(ac and not bc);abstain+=b is None
  status="JANE_REVIEW_CANDIDATE" if gains and not regressions and not abstain and len(groups)>=2 else "FLAY_MORE_EVIDENCE"
  p=dict(version="JANE-139",baseline_correct=bcorrect,candidate_correct=ncorrect,gains=gains,regressions=regressions,abstentions=abstain,status=status,jane_decision="UNDECIDED",learning_applied=False)
  self._event("COMPARE",dict(digest=digest(p)))
  return p
 def verify(self):
  prev="0"*64
  for i,e in enumerate(self.events):
   if e["seq"]!=i or e["prev"]!=prev or e["head"]!=digest({k:v for k,v in e.items() if k!="head"}):return False
   prev=e["head"]
  for path,c in self.cells.items():
   p=self.cells.get(path[:-1]) if path else None
   if path and (p is None or c.parent!=p.hash or (c.root,c.chronos)!=(p.root,p.chronos)):return False
   if c.hash!=digest(dict(path=c.path,parent=c.parent,root=c.root,chronos=c.chronos,rule=c.rule)):return False
  return True
def demo():
 x=Experiment()
 a=x.propose((),"upperleftrear","count_urls")
 b=x.propose((),"upperrightfront","root_aware")
 cases=[("mirror","holdout",("github","0root.ai"),("owned","owned"),False,"owned"),("wire","holdout",("a","b"),("wire","wire"),False,"wire"),("labs","holdout",("a","b"),("a","b"),True,"labs"),("archive","holdout",("a","b","c"),("archive",)*3,False,"archive")]
 return x,x.compare(a.path,b.path,cases)
if __name__=="__main__":
 x,r=demo();print(json.dumps({"result":r,"chain_valid":x.verify(),"event_count":len(x.events)},indent=2))
