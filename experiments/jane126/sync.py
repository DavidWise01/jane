"""JANE 126 — Chronos sync: coordinates never establish provenance."""
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import json
@dataclass(frozen=True)
class Chronos:
 year:int;month:int;day:int;hour:int;minute:int;second:int
 sign:str;degree:int;arcminute:int;arcsecond:int;offset_minutes:int
 def __post_init__(self):
  if self.sign not in ('+','-') or not 0<=self.degree<=360 or not 0<=self.arcminute<60 or not 0<=self.arcsecond<60 or (self.degree==360 and (self.arcminute or self.arcsecond)) or not -840<=self.offset_minutes<=840:raise ValueError("invalid Chronos")
  self.datetime()
 def datetime(self):
  return datetime(self.year,self.month,self.day,self.hour,self.minute,self.second,tzinfo=timezone(timedelta(minutes=self.offset_minutes)))
 def stamp(self):
  return f'{{{{ - {self.year:04d}:{self.month:02d}:{self.day:02d} || {self.hour:02d}:{self.minute:02d}:{self.second:02d} || {self.sign}{self.degree:03d}.{self.arcminute:02d}.{self.arcsecond:02d} || }}}}'
 def seconds(self):
  return int((self.datetime().astimezone(timezone.utc)-datetime(1970,1,1,tzinfo=timezone.utc)).total_seconds())
 def arcseconds(self):
  return (1 if self.sign=='+' else -1)*(3600*self.degree+60*self.arcminute+self.arcsecond)
@dataclass(frozen=True)
class Witness:
 id:str;surface:str;ancestry:str|None;custody:str|None;content_digest:str;chronos:Chronos;attested:bool=False
 def root(self):return 'owned:canonical' if self.surface in ('github','0root.ai') else self.ancestry
def compare(a,b,tolerance_seconds=0,tolerance_arcseconds=0):
 if a.id==b.id or not a.id or not b.id or not 0<=tolerance_seconds<=86400 or not 0<=tolerance_arcseconds<=1296000:raise ValueError("invalid input")
 dt=abs(a.chronos.seconds()-b.chronos.seconds())
 da=abs(a.chronos.arcseconds()-b.chronos.arcseconds())
 if a.root() is None or b.root() is None:status='UNKNOWN_ANCESTRY'
 elif a.root()==b.root():status='SHARED_RECORDED_ANCESTRY'
 elif not a.attested or not b.attested or not a.custody or not b.custody:status='CUSTODY_UNVERIFIED'
 elif a.custody==b.custody:status='SHARED_CUSTODY'
 else:status='SEPARATE_DECLARED_ROOTS_REVIEW'
 result=dict(version='JANE-126',witnesses=[a.id,b.id],delta_seconds=dt,delta_arcseconds=da,coordinates_close=(dt<=tolerance_seconds and da<=tolerance_arcseconds),same_content=a.content_digest==b.content_digest,status=status,jane_decision='UNDECIDED',learning_applied=False,limitation='Custody and attestation are supplied, not cryptographically verified.')
 result['digest']=sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
 return result
def demo():
 c=Chronos(2026,11,11,9,44,0,'+',123,45,56,-360)
 s=Chronos(2026,11,11,9,45,0,'+',123,46,0,-360)
 a=Witness('github','github','git','owned','a'*64,c,True)
 b=Witness('0root','0root.ai','web','owned','a'*64,s,True)
 x=Witness('external','internet','paper','external','b'*64,c,True)
 return dict(mirror=compare(a,b),outside=compare(a,x))
if __name__=='__main__':print(json.dumps(demo(),indent=2))
