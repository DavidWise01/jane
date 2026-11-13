"""JANE 152 compact GitHub reproduction; full 40-test version in downloadable ZIP."""
from dataclasses import dataclass
from hashlib import sha256
import json
CHRONOS='{{ 2026.11.13 }}{{ 10.07.00 }}{{ 123.45.56 }}'
def digest(x):return sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
@dataclass(frozen=True)
class Event:
 id:str;branch:str;operation:str;key:str;value:int=0;expected:int|None=None
def replay(start,events):
 s=dict(start);trace=[]
 for e in events:
  if e.operation=='add':s[e.key]=s.get(e.key,0)+e.value
  elif e.operation=='multiply':s[e.key]=s.get(e.key,0)*e.value
  elif e.operation=='set':s[e.key]=e.value
  elif e.operation=='delete':s.pop(e.key,None)
  elif e.operation=='require':
   if e.key not in s or s[e.key]!=e.expected:return dict(valid=False,terminal=None,trace=trace)
  elif e.operation=='set_if_absent':s.setdefault(e.key,e.value)
  else:raise ValueError('unknown operation')
  if len(s)>64 or any(abs(v)>1_000_000 for v in s.values()):return dict(valid=False,terminal=None,trace=trace)
  trace.append(dict(event=e.id,head=digest(s)))
 return dict(valid=True,terminal=s,trace=trace)
def compare(ancestor,a,b):
 a=tuple(a);b=tuple(b)
 if not a or not b or len(a)+len(b)>128 or len({e.id for e in a+b})!=len(a+b):raise ValueError('event budget')
 for e in a:
  if e.branch!='A':raise ValueError('branch A identity')
 for e in b:
  if e.branch!='B':raise ValueError('branch B identity')
 if any(e.operation not in ('add','multiply','set','delete','require','set_if_absent') or type(e.value)is not int for e in a+b):raise ValueError('event')
 ab=replay(ancestor,a+b);ba=replay(ancestor,b+a)
 status='ORDER_DEPENDENT_FAILURE' if not ab['valid'] or not ba['valid'] else 'NONCOMMUTING_BRANCHES' if ab['terminal']!=ba['terminal'] else 'COMPATIBLE_CONTINUATION_CANDIDATE'
 p=dict(version='JANE-152',chronos=CHRONOS,ancestor_digest=digest(ancestor),a=[e.__dict__ for e in a],b=[e.__dict__ for e in b],ab=ab,ba=ba,status=status,active='frozen_parent',learning_applied=False,jane_decision='UNDECIDED')
 p['digest']=digest(p);return p
def demo():
 return compare({'count':2},(Event('A1','A','add','count',3),),(Event('B1','B','multiply','count',2),))
if __name__=='__main__':print(json.dumps(demo(),indent=2))
