"""JANE 125: Chronos coordinate and bounded witness custody, offline prototype."""
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from hashlib import sha256
from ipaddress import ip_address
import json,re
PAT=re.compile(r'^\{\{ - (\d{4}):(\d{2}):(\d{2}) \|\| (\d{2}):(\d{2}):(\d{2}) \|\| ([+-])(\d{1,3})\.(\d{2})\.(\d{2}) \|\| \}\}$')
def digest(data):return sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
@dataclass(frozen=True)
class Chronos:
 year:int; month:int; day:int; hour:int; minute:int; second:int
 angle_sign:str; degree:int; arcminute:int; arcsecond:int; utc_offset_minutes:int
 def __post_init__(self):
  if self.angle_sign not in ('+','-') or not 0<=self.degree<=360 or not 0<=self.arcminute<60 or not 0<=self.arcsecond<60 or (self.degree==360 and (self.arcminute or self.arcsecond)):raise ValueError('angular coordinate')
  if not -840<=self.utc_offset_minutes<=840:raise ValueError('utc offset')
  datetime(self.year,self.month,self.day,self.hour,self.minute,self.second,tzinfo=timezone(timedelta(minutes=self.utc_offset_minutes)))
 @classmethod
 def parse(cls,text,utc_offset_minutes):
  m=PAT.fullmatch(text)
  if not m:raise ValueError('notation')
  a=list(m.groups())
  return cls(*map(int,a[:6]),a[6],*map(int,a[7:]),utc_offset_minutes)
 def render(self):
  return f'{{{{ - {self.year:04d}:{self.month:02d}:{self.day:02d} || {self.hour:02d}:{self.minute:02d}:{self.second:02d} || {self.angle_sign}{self.degree:03d}.{self.arcminute:02d}.{self.arcsecond:02d} || }}}}'
 def instant(self):
  return datetime(self.year,self.month,self.day,self.hour,self.minute,self.second,tzinfo=timezone(timedelta(minutes=self.utc_offset_minutes))).astimezone(timezone.utc).isoformat()
 def arcseconds(self):return (1 if self.angle_sign=='+' else -1)*(3600*self.degree+60*self.arcminute+self.arcsecond)
@dataclass(frozen=True)
class Receipt:
 witness_id:str; custody_root:str|None; head:str; sequence:int; coordinate:Chronos; signature_verified:bool=False
 def commitment(self):return digest(dict(id=self.witness_id,custody=self.custody_root,head=self.head,sequence=self.sequence,coordinate=self.coordinate.render(),offset=self.coordinate.utc_offset_minutes))
def verify(head,sequence,receipts):
 receipts=tuple(receipts)
 if not re.fullmatch('[0-9a-f]{64}',head) or sequence<0 or len(receipts)>32:raise ValueError('bounds')
 roots={};seen=set();issues=[]
 for r in receipts:
  if not r.witness_id or r.witness_id in seen:issues.append('duplicate-id');continue
  seen.add(r.witness_id)
  if not r.custody_root or not r.signature_verified:issues.append('unverified-custody');continue
  if not re.fullmatch('[0-9a-f]{64}',r.head) or r.sequence<0:issues.append('invalid-checkpoint');continue
  pair=(r.sequence,r.head)
  if r.custody_root in roots and roots[r.custody_root]!=pair:issues.append('custody-conflict')
  roots[r.custody_root]=pair
 matches=sum(x==(sequence,head) for x in roots.values())
 status=('WITNESS_CONFLICT' if 'custody-conflict' in issues or 'duplicate-id' in issues else
         'TRUNCATION_SUSPECTED' if any(s>sequence for s,h in roots.values()) else
         'FORK_SUSPECTED' if any(s==sequence and h!=head for s,h in roots.values()) else
         'THREE_CUSTODY_ROOT_MATCH' if matches>=3 and not issues else 'INSUFFICIENT_AUTHENTICATED_CUSTODY')
 return dict(status=status,matches=matches,issues=sorted(set(issues)),jane_decision='UNDECIDED',learning_applied=False,
             caveat='Signature flags and custody labels are supplied, not independently authenticated.')
