"""JANE 194: preregistered missingness analysis of beacon rounds.

Synthetic signed observation claims are not proof of physical availability.
"""
from __future__ import annotations
import hashlib, json, math
from dataclasses import dataclass
from typing import Tuple


def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def sha(x):return hashlib.sha256(canonical(x).encode()).hexdigest()

@dataclass(frozen=True)
class Plan:
    rounds:Tuple[int,...]
    deadline_ms:int
    observer_roots:Tuple[str,...]
    min_quorum:int=2
    def __post_init__(self):
        if not self.rounds or len(self.rounds)>512 or tuple(sorted(set(self.rounds)))!=self.rounds or self.rounds[0]<0:raise ValueError('invalid preregistered rounds')
        if self.deadline_ms<0 or self.min_quorum<1 or self.min_quorum>len(self.observer_roots) or len(set(self.observer_roots))!=len(self.observer_roots):raise ValueError('invalid observers/deadline')
    def record(self):return dict(rounds=self.rounds,deadline_ms=self.deadline_ms,observer_roots=self.observer_roots,min_quorum=self.min_quorum)

@dataclass(frozen=True)
class Observation:
    round:int
    observer_root:str
    status:str # published, absent, outage
    observed_ms:int
    evidence_hash:str
    def __post_init__(self):
        if self.status not in ('published','absent','outage') or self.round<0 or self.observed_ms<0:raise ValueError('invalid observation')
        if len(self.evidence_hash)!=64 or any(c not in '0123456789abcdef' for c in self.evidence_hash):raise ValueError('invalid evidence commitment')

class Audit:
    def __init__(self,plan:Plan):
        self.plan=plan;self.plan_digest=sha(plan.record());self.events=[];self.frozen=True;self.parent_active='frozen';self.append('PLAN',plan.record())
    def append(self,kind,details):
        event=dict(index=len(self.events),kind=kind,details=details,prev=self.events[-1]['head'] if self.events else '0'*64)
        event['head']=sha(event);self.events.append(event)
    def verify_chain(self,external_head=None):
        prev='0'*64
        for i,e in enumerate(self.events):
            if e['index']!=i or e['prev']!=prev or e['head']!=sha({k:v for k,v in e.items() if k!='head'}):return 'LOCAL_CHAIN_INVALID'
            prev=e['head']
        return 'EXTERNAL_HEAD_MISMATCH' if external_head is not None and prev!=external_head else 'LOCAL_CHAIN_VALID'
    def analyze(self,observations,now_ms,expected_baseline=None):
        if now_ms<0:raise ValueError('clock')
        if len(observations)>len(self.plan.rounds)*len(self.plan.observer_roots):raise ValueError('observation budget exceeded')
        byround={r:{} for r in self.plan.rounds}
        for o in observations:
            if o.round not in byround:raise ValueError('unregistered round')
            if o.observer_root not in self.plan.observer_roots:raise ValueError('unregistered root')
            if o.observer_root in byround[o.round]:raise ValueError('duplicate observer/round')
            byround[o.round][o.observer_root]=o
        rows=[]
        for r,items in byround.items():
            valid=[o for o in items.values() if o.observed_ms<=now_ms]
            pub=[o for o in valid if o.status=='published']
            absent=[o for o in valid if o.status=='absent' and o.observed_ms>=self.plan.deadline_ms]
            outage=[o for o in valid if o.status=='outage']
            if len(pub)>=self.plan.min_quorum and len(absent)>=self.plan.min_quorum:status='CONFLICTING_OBSERVATIONS'
            elif len(pub)>=self.plan.min_quorum:status='PUBLISHED_OBSERVED'
            elif len(absent)>=self.plan.min_quorum:status='NOT_OBSERVED_AFTER_DEADLINE'
            elif outage:status='OUTAGE_OR_INCOMPLETE'
            else:status='UNKNOWN_INCOMPLETE'
            rows.append(dict(round=r,status=status,published=len(pub),absent=len(absent),outage=len(outage),observed_roots=len(items)))
        n=len(rows)
        missing=sum(x['status']=='NOT_OBSERVED_AFTER_DEADLINE' for x in rows)
        published=sum(x['status']=='PUBLISHED_OBSERVED' for x in rows)
        unresolved=n-published-missing
        # This is a descriptive maximum run in the preregistered ORDER, not an intent attribution.
        cur=longest=0
        for row in rows:
            cur=cur+1 if row['status']=='NOT_OBSERVED_AFTER_DEADLINE' else 0
            longest=max(longest,cur)
        # If a declared baseline probability exists, compute exact binomial upper tail
        # on *resolved rounds only*: never treat unknown rounds as absent successes.
        pvalue=None
        if expected_baseline is not None:
            if not isinstance(expected_baseline,(int,float)) or not math.isfinite(expected_baseline) or not 0<=expected_baseline<=1:raise ValueError('baseline')
            resolved=published+missing
            if resolved:
                pvalue=sum(math.comb(resolved,k)*(expected_baseline**k)*((1-expected_baseline)**(resolved-k)) for k in range(missing,resolved+1))
        result=dict(id='JANE-194',plan_digest=self.plan_digest,rounds_total=n,published=published,missing=missing,unresolved=unresolved,missing_fraction_all=missing/n,longest_missing_run=longest,baseline_missing_probability=expected_baseline,binomial_upper_tail_resolved=pvalue,rows=rows,scope='declared local fixture observations',intent_proven=False,independent_physical_roots_verified=False,parent_active=self.parent_active,learning_applied=False)
        result['digest']=sha(result)
        self.append('ANALYSIS',dict(result_digest=result['digest'],counts=[published,missing,unresolved],longest_missing_run=longest))
        return result

def fixture(statuses,root_names=('a','b','c')):
    plan=Plan(tuple(range(40,40+len(statuses))),100,root_names)
    obs=[]
    for round_id,status in zip(plan.rounds,statuses):
        if status=='unknown':continue
        for root in root_names:
            obs.append(Observation(round_id,root,status,120,sha([round_id,root,status])))
    return plan,obs

def demo():
    plan,obs=fixture(['published','absent','absent','published','absent','outage','published','absent'])
    a=Audit(plan); result=a.analyze(obs,200,expected_baseline=.2)
    return dict(result=result,chain=a.verify_chain(),event_count=len(a.events))
if __name__=='__main__':print(json.dumps(demo(),indent=2))