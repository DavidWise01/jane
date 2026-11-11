"""JANE 127: chronology is not causality; offline Chronos evaluator."""
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from hashlib import sha256
import json
@dataclass(frozen=True)
class Chronos:
 y:int;m:int;d:int;h:int;mi:int;s:int;sign:str;deg:int;arcmin:int;arcsec:int;offset:int=0
 def utc(self):
  if self.sign not in ('+','-') or not 0<=self.deg<=360 or not 0<=self.arcmin<60 or not 0<=self.arcsec<60 or not -840<=self.offset<=840:raise ValueError('Chronos bounds')
  return datetime(self.y,self.m,self.d,self.h,self.mi,self.s,tzinfo=timezone(timedelta(minutes=self.offset))).astimezone(timezone.utc)
 def render(self):return f'{{{{ - {self.y:04}:{self.m:02}:{self.d:02} || {self.h:02}:{self.mi:02}:{self.s:02} || {self.sign}{self.deg:03}.{self.arcmin:02}.{self.arcsec:02} || }}}}'
@dataclass(frozen=True)
class Estimate:
 chronos:Chronos
 uncertainty:int=0
 def bounds(self):
  if not 0<=self.uncertainty<=86400:raise ValueError('uncertainty')
  t=self.chronos.utc();u=timedelta(seconds=self.uncertainty);return t-u,t+u
@dataclass(frozen=True)
class Report:
 id:str;event_id:str;event:Estimate|None;observed:Estimate;received:Estimate;root:str|None;custody:str|None
def order(a,b):
 al,au=a.bounds();bl,bu=b.bounds()
 return 'A_BEFORE_B' if au<bl else 'B_BEFORE_A' if bu<al else 'ORDER_UNRESOLVED'
def compare(a,b):
 if not a.id or not b.id or a.id==b.id:raise ValueError('report identifiers')
 result=dict(version='JANE-127',observation_order=order(a.observed,b.observed),receipt_order=order(a.received,b.received),
  event_order=order(a.event,b.event) if a.event and b.event else 'EVENT_TIME_UNKNOWN',
  ancestry='UNKNOWN' if a.root is None or b.root is None else 'SHARED' if a.root==b.root else 'SEPARATE_DECLARED',
  custody='UNKNOWN' if a.custody is None or b.custody is None else 'SHARED' if a.custody==b.custody else 'SEPARATE_DECLARED',
  same_claimed_event=a.event_id==b.event_id,jane_decision='UNDECIDED',learning_applied=False,
  caveat='Synthetic supplied clocks, roots and custodians; coordinate order is not causal proof.')
 result['digest']=sha256(json.dumps(result,sort_keys=True).encode()).hexdigest();return result
def demo():
 def c(s):return Chronos(2026,11,11,14,0,s,'+',123,45,56,-360)
 a=Report('A','E',None,Estimate(c(10)),Estimate(c(20)),'owned:canonical','owned')
 b=Report('B','E',None,Estimate(c(15)),Estimate(c(30)),'external:paper','external')
 return compare(a,b)
if __name__=='__main__':print(json.dumps(demo(),indent=2))
