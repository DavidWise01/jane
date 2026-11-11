"""JANE 128 · Chronos causal witness (offline, review-only)."""
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import json

@dataclass(frozen=True)
class Chronos:
 year:int;month:int;day:int;hour:int;minute:int;second:int
 sign:str;degree:int;arcminute:int;arcsecond:int;offset:int=0
 def utc(self):
  if self.sign not in ('+','-') or not 0<=self.degree<=360 or not 0<=self.arcminute<60 or not 0<=self.arcsecond<60 or not -840<=self.offset<=840:raise ValueError('chronos bounds')
  return datetime(self.year,self.month,self.day,self.hour,self.minute,self.second,tzinfo=timezone(timedelta(minutes=self.offset))).astimezone(timezone.utc)
 def stamp(self):return f'{{{{ - {self.year:04}:{self.month:02}:{self.day:02} || {self.hour:02}:{self.minute:02}:{self.second:02} || {self.sign}{self.degree:03}.{self.arcminute:02}.{self.arcsecond:02} || }}}}'
@dataclass(frozen=True)
class Event:
 id:str;at:Chronos;uncertainty:int=0
 def interval(self):
  if not 0<=self.uncertainty<=86400:raise ValueError('uncertainty')
  t=self.at.utc();u=timedelta(seconds=self.uncertainty);return t-u,t+u
@dataclass(frozen=True)
class Edge:
 source:str;target:str;kind:str;witness:str;ancestry:str|None;proof_hash:str|None

def inspect(events,edges):
 events=tuple(events);edges=tuple(edges)
 if len(events)>128 or len(edges)>256:raise ValueError('budget')
 if any(not e.id for e in events) or len({e.id for e in events})!=len(events):raise ValueError('ids')
 nodes={e.id:e for e in events};adj={k:[] for k in nodes}
 for e in events:e.interval()
 for link in edges:
  if link.source not in nodes or link.target not in nodes or link.source==link.target or not link.witness or link.kind not in ('dependency','causal_claim'):raise ValueError('edge')
  adj[link.source].append(link.target)
 seen={k:0 for k in nodes}
 def visit(k):
  seen[k]=1
  for nxt in adj[k]:
   if seen[nxt]==1 or (seen[nxt]==0 and visit(nxt)):return True
  seen[k]=2;return False
 cyclic=any(seen[k]==0 and visit(k) for k in sorted(nodes))
 checks=[]
 for link in edges:
  start=nodes[link.source].interval();end=nodes[link.target].interval()
  contradiction=start[0]>end[1]
  proven=bool(link.ancestry and link.proof_hash and len(link.proof_hash)==64 and all(x in '0123456789abcdef' for x in link.proof_hash))
  verdict='TEMPORAL_CONTRADICTION' if contradiction else 'MISSING_PROVENANCE' if not proven else 'CAUSAL_CLAIM_REVIEW' if link.kind=='causal_claim' else 'RECORDED_DEPENDENCY'
  checks.append(dict(source=link.source,target=link.target,verdict=verdict,certain_order=start[1]<end[0]))
 status='CYCLE_REJECTED' if cyclic else 'CONTRADICTION_REVIEW' if any(c['verdict']=='TEMPORAL_CONTRADICTION' for c in checks) else 'EVIDENCE_INCOMPLETE' if any(c['verdict']=='MISSING_PROVENANCE' for c in checks) else 'JANE_REVIEW_REQUIRED'
 result=dict(version='JANE-128',status=status,cycle=cyclic,checks=checks,roots=sorted({l.ancestry for l in edges if l.ancestry}),jane_decision='UNDECIDED',learning_applied=False,caveat='Documented dependency is not proof of physical causality; ancestry is declared.')
 result['digest']=sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
 return result
