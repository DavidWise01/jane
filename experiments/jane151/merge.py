"""JANE 151: immutable, evidence-carrying two-parent reconciliation proposals.

Offline deterministic fixture model; custody endorsements are untrusted claims.
A merge is a proposal referencing both histories, never a rewritten chain.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json

CHRONOS = '{{ 2026.11.13 }}{{ 07.28.00 }}{{ 123.45.56 }}'
ZERO = '0'*64
MAX_EVENTS = 256

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8')

def digest(value):
    return sha256(canonical(value)).hexdigest()

def hex_digest(value):
    return isinstance(value, str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)

@dataclass(frozen=True)
class Event:
    sequence: int
    payload: str
    predecessor: str
    head: str

    @classmethod
    def build(cls, sequence: int, payload: str, predecessor: str):
        if not isinstance(sequence,int) or sequence < 0 or not isinstance(payload,str) or not payload or not hex_digest(predecessor):
            raise ValueError('event inputs')
        head = digest({'sequence':sequence,'payload':payload,'predecessor':predecessor})
        return cls(sequence,payload,predecessor,head)

@dataclass(frozen=True)
class Branch:
    branch_id: str
    events: tuple[Event,...]
    custody_roots: tuple[str,...]
    chronos: str = CHRONOS

    @property
    def head(self):
        return self.events[-1].head if self.events else ZERO

    def verified(self):
        if not self.branch_id or not self.chronos or len(self.events)>MAX_EVENTS:
            return False
        prev = ZERO
        for i,e in enumerate(self.events):
            if e.sequence != i or e.predecessor != prev or e.head != digest({'sequence':i,'payload':e.payload,'predecessor':prev}):
                return False
            prev = e.head
        return True

def build_branch(branch_id, payloads, custody_roots=()):
    events=[]
    for payload in payloads:
        events.append(Event.build(len(events),payload,events[-1].head if events else ZERO))
    return Branch(branch_id,tuple(events),tuple(custody_roots))

class Merger:
    def __init__(self):
        self.events=[]
        self.proposals={}
        self.active='frozen_parent'

    def _record(self,kind,data):
        item={'sequence':len(self.events),'kind':kind,'data':data,
              'previous':self.events[-1]['head'] if self.events else ZERO}
        item['head']=digest(item)
        self.events.append(item)
        return item['head']

    def propose(self,left:Branch,right:Branch,claimed_ancestor=None):
        if not isinstance(left,Branch) or not isinstance(right,Branch):
            raise ValueError('branches')
        if left.branch_id == right.branch_id or not left.verified() or not right.verified():
            self._record('REJECT',{'reason':'INVALID_OR_SAME_BRANCH'})
            return {'status':'INVALID_OR_SAME_BRANCH','learning_applied':False,'jane_decision':'UNDECIDED'}
        upto=min(len(left.events),len(right.events))
        shared=0
        while shared<upto and left.events[shared]==right.events[shared]:
            shared+=1
        ancestor=left.events[shared-1].head if shared else ZERO
        if claimed_ancestor is not None and claimed_ancestor!=ancestor:
            self._record('REJECT',{'reason':'FALSE_COMMON_ANCESTOR','claimed':claimed_ancestor,'actual':ancestor})
            return {'status':'FALSE_COMMON_ANCESTOR','learning_applied':False,'jane_decision':'UNDECIDED'}
        left_tail=left.events[shared:];right_tail=right.events[shared:]
        if not shared:
            status='NO_SHARED_EVENT_ANCESTOR'
        elif not left_tail or not right_tail:
            status='PREFIX_RELATION_NOT_FORK'
        elif left.events[shared].head==right.events[shared].head:
            status='INVALID_DIVERGENCE'
        else:
            status='TWO_PARENT_REVIEW_PROPOSAL'
        roots_left=tuple(sorted(set(left.custody_roots)))
        roots_right=tuple(sorted(set(right.custody_roots)))
        # Custody names are provenance declarations, never evidence of independence.
        body={
            'version':'JANE-151','chronos':CHRONOS,'status':status,
            'ancestor_sequence':shared-1,'ancestor_head':ancestor,
            'parents':sorted([{'branch':left.branch_id,'head':left.head,'tail_heads':[e.head for e in left_tail],
                               'declared_roots':list(roots_left)},
                              {'branch':right.branch_id,'head':right.head,'tail_heads':[e.head for e in right_tail],
                               'declared_roots':list(roots_right)}],key=lambda p:p['branch']),
            'shared_events':shared,'preserved_event_references':len(left.events)+len(right.events)-shared,
            'independent_witnesses_verified':0,'evidence_authenticated':False,
            'active':self.active,'learning_applied':False,'jane_decision':'UNDECIDED',
            'caveat':'Locally built hash chains and declared roots, not independently authenticated custody.'
        }
        body['proposal_digest']=digest(body)
        if body['proposal_digest'] not in self.proposals:
            self.proposals[body['proposal_digest']]=body
            self._record('PROPOSE',{'digest':body['proposal_digest'],'status':status})
        return json.loads(json.dumps(body))

    def audit(self,expected_head=None):
        previous=ZERO
        for i,e in enumerate(self.events):
            if e['sequence']!=i or e['previous']!=previous or e['head']!=digest({k:v for k,v in e.items() if k!='head'}):
                return 'TAMPERED'
            previous=e['head']
        if expected_head is not None and expected_head!=previous:
            return 'EXTERNAL_HEAD_MISMATCH'
        for h,body in self.proposals.items():
            if h!=digest({k:v for k,v in body.items() if k!='proposal_digest'}):
                return 'PROPOSAL_TAMPERED'
        return 'VALID_LOCAL_CHAIN'

def demo():
    common=('GENESIS','OBSERVE 001','OBSERVE 002','CHECKPOINT 003')
    a=build_branch('MESH-A',common+('EVENT 004 A','EVENT 005 A'),('owned:canonical','external:A','external:B'))
    b=build_branch('MESH-B',common+('EVENT 004 B','EVENT 005 B'),('external:C','external:D'))
    m=Merger()
    result=m.propose(a,b,a.events[3].head)
    return m,result,a,b

if __name__=='__main__':
    m,result,a,b=demo()
    print(json.dumps({'proposal':result,'audit':m.audit()},indent=2))
