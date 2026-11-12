"""FLAY 137: Chronos time × nine anchors in 3x3x3. Offline, review-only."""
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from hashlib import sha256
import json,re
ANCHORS={"upperleftrear":(-1,1,-1),"centerrear":(0,0,-1),"lowerleftrear":(-1,-1,-1),
"centerupper":(0,1,0),"center":(0,0,0),"centerlower":(0,-1,0),
"upperrightfront":(1,1,1),"rightcenter":(1,0,1),"lowerrightfront":(1,-1,1)}
PAT=re.compile(r"^\{\{ (\d{4})\.(\d{1,2})\.(\d{1,2}) \}\}\{\{ (\d{1,2})\.(\d{1,2})\.(\d{1,2}) \}\}\{\{ ([+-]?\d{1,3})\.(\d{1,2})\.(\d{1,2}) \}\}\{\{ ([a-z]+) \}\}$")
def hashit(x):return sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class Coordinate:
 year:int;month:int;day:int;hour:int;minute:int;second:int
 degree:int;arcminute:int;arcsecond:int;anchor:str;offset:int=0
 def __post_init__(self):
  if self.anchor not in ANCHORS or not -840<=self.offset<=840 or not -360<=self.degree<=360 or not 0<=self.arcminute<60 or not 0<=self.arcsecond<60 or (abs(self.degree)==360 and (self.arcminute or self.arcsecond)):raise ValueError("bounds")
  self.utc()
 def utc(self):
  return datetime(self.year,self.month,self.day,self.hour,self.minute,self.second,tzinfo=timezone(timedelta(minutes=self.offset))).astimezone(timezone.utc).isoformat()
 def render(self):
  return f"{{{{ {self.year:04d}.{self.month:02d}.{self.day:02d} }}}}{{{{ {self.hour:02d}.{self.minute:02d}.{self.second:02d} }}}}{{{{ {self.degree}.{self.arcminute:02d}.{self.arcsecond:02d} }}}}{{{{ {self.anchor} }}}}"
 @classmethod
 def parse(cls,s,offset=0):
  m=PAT.fullmatch(s)
  if not m:raise ValueError("syntax")
  v=m.groups()
  return cls(*map(int,v[:9]),v[9],offset)
 def xyz(self):return ANCHORS[self.anchor]
@dataclass(frozen=True)
class Observation:
 question:str;distinction:str;coord:Coordinate;surface:str;source_root:str|None;sha:str|None
 def packet(self):
  if not self.question or not self.distinction or self.sha and not re.fullmatch("[0-9a-f]{64}",self.sha):raise ValueError("observation")
  root="owned:canonical" if self.surface in ("github","0root.ai") else self.source_root
  p=dict(version="FLAY-137",address=self.coord.render(),utc=self.coord.utc(),offset=self.coord.offset,xyz=self.coord.xyz(),question=self.question,missing_distinction=self.distinction,source=self.surface,ancestry=root,evidence_sha256=self.sha,state="JANE_REVIEW" if root else "REQUEST_ANCESTRY",learning_applied=False,jane_decision="UNDECIDED")
  p["digest"]=hashit(p)
  return p
class Ledger:
 def __init__(self):self.events=[]
 def append(self,obs):
  p=obs.packet();seq=len(self.events);prev=self.events[-1]["head"] if seq else "0"*64
  e=dict(seq=seq,prev=prev,packet=p);e["head"]=hashit(e)
  self.events.append(e);return json.loads(json.dumps(e))
 def verify(self,external_head=None):
  prev="0"*64
  for i,e in enumerate(self.events):
   if e["seq"]!=i or e["prev"]!=prev or e["head"]!=hashit({k:v for k,v in e.items() if k!="head"}):return "TAMPERED"
   prev=e["head"]
  return "EXTERNAL_HEAD_MISMATCH" if external_head is not None and external_head!=prev else "VALID_LOCAL_CHAIN"
