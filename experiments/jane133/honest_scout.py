"""JANE 133: offline honest-scout calibration. No autonomous learning."""
from dataclasses import dataclass
from fractions import Fraction as F
from hashlib import sha256
import json
OWNED={"github","0root.ai"}
def root(surface,declared):return "owned:canonical" if surface in OWNED else declared
@dataclass(frozen=True)
class Prediction:
 id:str;scout:str;expected_gain:F;cost:int;chronos:str;surface:str;origin:str|None
@dataclass(frozen=True)
class Outcome:
 prediction_id:str;actual_gain:F;chronos:str;surface:str;origin:str|None;verified:bool=False
class Ledger:
 def __init__(self):self.predictions={};self.outcomes={};self.events=[]
 def predict(self,p):
  if not p.id or not p.scout or p.id in self.predictions or p.cost<=0 or not 0<=p.expected_gain<=1 or not p.chronos:raise ValueError("prediction")
  self.predictions[p.id]=p;self.events.append(("PREDICT",p.id))
 def observe(self,o):
  if o.prediction_id not in self.predictions or o.prediction_id in self.outcomes or not 0<=o.actual_gain<=1 or not o.chronos:raise ValueError("outcome")
  self.outcomes[o.prediction_id]=o;self.events.append(("OBSERVE",o.prediction_id))
 def report(self,min_verified=2):
  if not 1<=min_verified<=32:raise ValueError("minimum")
  groups={}
  for id,p in sorted(self.predictions.items()):
   g=groups.setdefault(p.scout,{"v":[],"unverified":0,"pending":0})
   o=self.outcomes.get(id)
   if o is None:g["pending"]+=1;continue
   independent=o.verified and root(o.surface,o.origin) and root(p.surface,p.origin) and root(o.surface,o.origin)!=root(p.surface,p.origin)
   if independent:g["v"].append(abs(p.expected_gain-o.actual_gain))
   else:g["unverified"]+=1
  scores={}
  for name,g in sorted(groups.items()):
   n=len(g["v"]);err=sum(g["v"],F())/n if n else None
   scores[name]={"verified_count":n,"unverified_count":g["unverified"],"pending_count":g["pending"],"mean_absolute_error":str(err) if err is not None else None,
    "status":"NEEDS_VERIFIED_OUTCOMES" if n<min_verified else "RECALIBRATE" if err>F(1,4) else "CALIBRATED_ON_FIXTURES"}
  result={"version":"JANE-133","scouts":scores,"events":self.events,"learning_applied":False,"jane_decision":"UNDECIDED",
   "limitation":"Witness verification flags and ancestry roots are supplied synthetic claims, not cryptographically authenticated."}
  result["digest"]=sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
  return result
def demo():
 t="{{ - 2026:11:11 || 18:58:00 || +123.45.56 || }}"
 l=Ledger()
 for scout in ("lineage","copies"):
  for i in range(2):
   id=f"{scout}-{i}"
   l.predict(Prediction(id,scout,F(3,4),2,t,"github","owned"))
   l.observe(Outcome(id,F(3,4) if scout=="lineage" else F(0),t,"internet",f"witness-{scout}-{i}",True))
 return l.report()
if __name__=="__main__":print(json.dumps(demo(),indent=2))
