"""JANE 149: offline returning-witness continuity verification."""
from dataclasses import dataclass
from hashlib import sha256
import json

def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

@dataclass(frozen=True)
class Checkpoint:
    sequence:int
    head:str
    custody_root:str
    chronos:str

@dataclass(frozen=True)
class Link:
    sequence:int
    previous:str
    event_digest:str
    head:str

def make_link(sequence,previous,event_digest):
    if sequence < 0 or len(previous)!=64 or len(event_digest)!=64:
        raise ValueError('link')
    head=digest(dict(sequence=sequence,previous=previous,event_digest=event_digest))
    return Link(sequence,previous,event_digest,head)

class FLAY:
    def __init__(self,checkpoints,max_links=64):
        self.checkpoints=dict(checkpoints)
        if not 1<=max_links<=1024:raise ValueError('proof budget')
        if any(k!=v.custody_root or v.sequence<0 or len(v.head)!=64 or not v.chronos for k,v in self.checkpoints.items()):raise ValueError('checkpoint')
        self.max_links=max_links;self.outages={};self.events=[];self.active='frozen_parent'
    def _event(self,kind,data):
        e=dict(index=len(self.events),kind=kind,data=data,previous=self.events[-1]['hash'] if self.events else '0'*64)
        e['hash']=digest(e);self.events.append(e)
    def offline(self,root,when,reason):
        if root not in self.checkpoints or root in self.outages or not when or not reason:raise ValueError('outage')
        self.outages[root]=when;self._event('OFFLINE',dict(root=root,when=when,reason=reason))
    def returned(self,root,checkpoint,links,observed_at):
        if root not in self.outages or not observed_at:raise ValueError('unregistered return')
        old=self.checkpoints[root];links=tuple(links)
        if checkpoint.custody_root!=root or not checkpoint.chronos or len(checkpoint.head)!=64 or checkpoint.sequence<0:status='BAD_CLAIM'
        elif checkpoint.sequence<old.sequence:status='STALE_RETURN'
        elif checkpoint.sequence==old.sequence:status='UNCHANGED' if checkpoint.head==old.head else 'FORK'
        elif len(links)>self.max_links:status='PROOF_BUDGET_EXCEEDED'
        elif len(links)!=checkpoint.sequence-old.sequence:status='MISSING_LINKS'
        else:
            prev=old.head;seq=old.sequence+1;status='CATCHUP_ACCEPTED'
            for link in links:
                if link.sequence!=seq or link.previous!=prev or len(link.event_digest)!=64 or link.head!=digest(dict(sequence=seq,previous=prev,event_digest=link.event_digest)):
                    status='BROKEN_CONTINUITY';break
                seq+=1;prev=link.head
            if status=='CATCHUP_ACCEPTED' and prev!=checkpoint.head:status='FORK'
        self._event('RETURN',dict(root=root,from_sequence=old.sequence,to_sequence=checkpoint.sequence,status=status,observed_at=observed_at,head=checkpoint.head))
        if status in ('UNCHANGED','CATCHUP_ACCEPTED'):
            if status=='CATCHUP_ACCEPTED':self.checkpoints[root]=checkpoint
            del self.outages[root]
        return dict(status=status,from_sequence=old.sequence,to_sequence=checkpoint.sequence,active=self.active,learning_applied=False,jane_decision='UNDECIDED')
    def audit(self,external_head=None):
        prev='0'*64
        for i,e in enumerate(self.events):
            if e['index']!=i or e['previous']!=prev or e['hash']!=digest({k:v for k,v in e.items() if k!='hash'}):return 'TAMPERED'
            prev=e['hash']
        return 'EXTERNAL_HEAD_MISMATCH' if external_head is not None and prev!=external_head else 'VALID_LOCAL_CHAIN'

def demo():
    ts='{{ 2026.11.12 }}{{ 22.02.00 }}{{ 123.45.56 }}'
    old=Checkpoint(4,'a'*64,'external:A',ts)
    f=FLAY({'external:A':old});f.offline('external:A',ts,'simulated outage')
    first=make_link(5,old.head,'b'*64);second=make_link(6,first.head,'c'*64)
    return f,f.returned('external:A',Checkpoint(6,second.head,'external:A',ts),(first,second),ts)
if __name__=='__main__':
    f,result=demo();print(json.dumps(dict(result=result,audit=f.audit()),indent=2))
