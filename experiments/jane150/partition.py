"""JANE 150: bounded partition lineage reconciliation, synthetic evidence only."""
from dataclasses import dataclass
from hashlib import sha256
import json

CHRONOS = '{{ 2026.11.13 }}{{ 07.28.00 }}{{ 123.45.56 }}'
GENESIS = '0'*64

def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()

def digest(x):
    return sha256(canonical(x)).hexdigest()

@dataclass(frozen=True)
class Event:
    sequence:int
    payload:str
    previous:str
    head:str

def extend(chain,payload):
    chain=tuple(chain)
    prior=chain[-1].head if chain else GENESIS
    seq=len(chain)
    head=digest({'sequence':seq,'payload':payload,'previous':prior})
    return chain+(Event(seq,payload,prior,head),)

def validate(chain,max_length=128):
    if not isinstance(chain,(tuple,list)) or len(chain)>max_length:return False
    previous=GENESIS
    for seq,e in enumerate(chain):
        if not isinstance(e,Event) or e.sequence!=seq or e.previous!=previous or not isinstance(e.payload,str) or not e.payload or e.head!=digest({'sequence':seq,'payload':e.payload,'previous':previous}):return False
        previous=e.head
    return True

@dataclass(frozen=True)
class Claim:
    branch:str
    root:str
    administration:str
    sequence:int
    head:str
    signature_checked:bool=False
    chronos:str=CHRONOS

def canonical_root(root):
    return 'owned:canonical' if root in ('github','0root.ai','owned:canonical') else root

class Partition:
    def __init__(self,branches,claims,required=3):
        self.branches={k:tuple(v) for k,v in branches.items()}
        self.claims=tuple(claims)
        if not 1<=required<=16 or not 1<=len(self.branches)<=8 or len(self.claims)>128:raise ValueError('budget')
        if any(not k or not validate(v) for k,v in self.branches.items()):raise ValueError('bad history')
        self.required=required
        self.events=[]
        self._record('DECLARE',{'branches':sorted(self.branches),'threshold':required})
    def _record(self,kind,detail):
        e={'sequence':len(self.events),'kind':kind,'detail':detail,'previous':self.events[-1]['head'] if self.events else GENESIS}
        e['head']=digest(e)
        self.events.append(e)
    def audit(self,external_head=None):
        prev=GENESIS
        for i,e in enumerate(self.events):
            if e['sequence']!=i or e['previous']!=prev or e['head']!=digest({k:v for k,v in e.items() if k!='head'}):return 'TAMPERED'
            prev=e['head']
        return 'EXTERNAL_HEAD_MISMATCH' if external_head is not None and external_head!=prev else 'VALID_LOCAL_CHAIN'
    def assess(self):
        names=sorted(self.branches)
        if len(names)!=2:raise ValueError('exactly two comparison branches required')
        a,b=(self.branches[k] for k in names)
        common=0
        while common<min(len(a),len(b)) and a[common].head==b[common].head:common+=1
        prefix=a[:common]
        ancestor={'sequence':common-1,'head':prefix[-1].head if prefix else GENESIS}
        branch_info={}
        root_claims={}
        for c in self.claims:
            if c.branch not in self.branches or not c.root or not c.administration or not c.chronos or c.sequence<0:raise ValueError('claim')
            if c.signature_checked:
                root=canonical_root(c.root)
                if root in root_claims and root_claims[root][0]!=c.administration:
                    root_claims[root][1].add('ADMIN_CONFLICT')
                else:
                    if root not in root_claims:root_claims[root]=(c.administration,set())
                root_claims[root][1].add((c.branch,c.sequence,c.head))
        invalid_roots={root for root,(_,claims) in root_claims.items() if len(claims)>1}
        for name in names:
            chain=self.branches[name]
            head=chain[-1].head if chain else GENESIS
            supporters=[]
            for root,(admin,claims) in root_claims.items():
                if root not in invalid_roots and (name,len(chain)-1,head) in claims:
                    supporters.append((root,admin))
            distinct_admins=len({admin for _,admin in supporters})
            branch_info[name]={'sequence':len(chain)-1,'head':head,'post_ancestor_events':len(chain)-common,'eligible_root_count':len(supporters),'eligible_administrators':distinct_admins,'fixture_quorum':distinct_admins>=self.required}
        if a==b:status='SAME_HISTORY'
        elif common==len(a) or common==len(b):status='PREFIX_CONTINUATION'
        else:status='PARTITION_FORK'
        result={'version':'JANE-150','chronos':CHRONOS,'status':status,'ancestor':ancestor,'branches':branch_info,'disqualified_roots':sorted(invalid_roots),'preserve_both':True,'automatic_merge':False,'active':'frozen_parent','learning_applied':False,'jane_decision':'UNDECIDED','limitations':'Signatures, operator identities and witness independence supplied as fixture claims; not authenticated live custodians.'}
        result['digest']=digest(result)
        self._record('RECONCILE',{'result_digest':result['digest'],'status':status})
        return result

def demo():
    prefix=()
    for label in ('freeze','observe','checkpoint','ack'):
        prefix=extend(prefix,label)
    left=extend(extend(prefix,'mesh-A-4'),'mesh-A-5')
    right=extend(extend(prefix,'mesh-B-4'),'mesh-B-5')
    claims=[]
    for name,chain,roots in [('A',left,('owned:canonical','external:A1','external:A2')),('B',right,('external:B1','external:B2'))]:
        for root in roots:
            claims.append(Claim(name,root,root,len(chain)-1,chain[-1].head,True))
    p=Partition({'A':left,'B':right},claims)
    return p,p.assess()

if __name__=='__main__':
    p,r=demo();print(json.dumps({'result':r,'audit':p.audit()},indent=2))
