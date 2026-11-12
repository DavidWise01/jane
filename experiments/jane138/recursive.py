"""JANE 138 compact recursive FLAY address kernel. Offline, review-only."""
from dataclasses import dataclass
from hashlib import sha256
import json
ANCHORS={'upperleftrear':(-1,1,-1),'centerrear':(0,0,-1),'lowerleftrear':(-1,-1,-1),'centerupper':(0,1,0),'center':(0,0,0),'centerlower':(0,-1,0),'upperrightfront':(1,1,1),'rightcenter':(1,0,1),'lowerrightfront':(1,-1,1)}
def digest(v):return sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
@dataclass(frozen=True)
class Cell:
 path:tuple;chronos:str;source_root:str;evidence_hash:str;parent_hash:str|None;hash:str
class Memory:
 def __init__(self,chronos,source_root,evidence_hash):
  if not chronos or not source_root or len(evidence_hash)!=64:raise ValueError('root evidence')
  self.cells={};self.events=[];self._put((),chronos,source_root,evidence_hash,None)
 def _put(self,path,t,root,evidence,parent):
  data=dict(path=path,chronos=t,source_root=root,evidence_hash=evidence,parent_hash=parent)
  c=Cell(path,t,root,evidence,parent,digest(data));self.cells[path]=c
  e=dict(seq=len(self.events),path=path,cell_hash=c.hash,prev=self.events[-1]['head'] if self.events else '0'*64)
  e['head']=digest(e);self.events.append(e);return c
 def grow(self,parent,anchor):
  if parent not in self.cells or anchor not in ANCHORS:raise ValueError('address')
  path=parent+(anchor,)
  if path in self.cells or len(path)>8 or len(self.cells)>=729:raise ValueError('growth bound')
  p=self.cells[parent];return self._put(path,p.chronos,p.source_root,p.evidence_hash,p.hash)
 def verify(self,external_head=None):
  prev='0'*64
  for i,e in enumerate(self.events):
   if e['seq']!=i or e['prev']!=prev or digest({k:v for k,v in e.items() if k!='head'})!=e['head']:return 'TAMPERED'
   c=self.cells.get(e['path'])
   if not c:return 'MISSING_CELL'
   par=self.cells.get(c.path[:-1]) if c.path else None
   expected=par.hash if par else None
   if c.parent_hash!=expected or c.hash!=digest(dict(path=c.path,chronos=c.chronos,source_root=c.source_root,evidence_hash=c.evidence_hash,parent_hash=expected)) or c.hash!=e['cell_hash']:return 'CELL_TAMPERED'
   if par and (c.chronos,c.source_root,c.evidence_hash)!=(par.chronos,par.source_root,par.evidence_hash):return 'BROKEN_INHERITANCE'
   prev=e['head']
  if len(self.events)!=len(self.cells):return 'UNLOGGED_CELL'
  return 'EXTERNAL_HEAD_MISMATCH' if external_head and external_head!=prev else 'VALID'
 def packet(self,path):
  c=self.cells[path]
  return dict(version='JANE-138',chronos=c.chronos,address='/'.join(path) or 'ROOT',xyz=[ANCHORS[p] for p in path],root=c.source_root,independent_witness_increment=0,learning_applied=False,jane_decision='UNDECIDED')
def demo():
 m=Memory('{{ 2026.11.12 }}{{ 07.18.00 }}{{ 123.45.56 }}','owned:canonical','a'*64)
 p=()
 for anchor in ('center','upperleftrear','upperrightfront'):m.grow(p,anchor);p+=(anchor,)
 return m
if __name__=='__main__':
 m=demo();print(json.dumps(dict(status=m.verify(),count=len(m.cells),packet=m.packet(('center','upperleftrear','upperrightfront'))),indent=2))
