"""JANE 176: deterministic, evidence-preserving comparison-policy replay.

Models comparison of immutable experimental evidence, not physical verification.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import re


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def digest(value):
    return sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class Evidence:
    original_value: int
    repeated_value: int
    same_question: bool
    same_selection: bool
    distinct_declared_roots: bool
    original_capture: str
    repeat_capture: str

    def __post_init__(self):
        if type(self.original_value) is not int or type(self.repeated_value) is not int:
            raise ValueError('integer values required')
        for k in ('same_question','same_selection','distinct_declared_roots'):
            if type(getattr(self,k)) is not bool:
                raise ValueError('boolean protocol attributes required')
        for k in ('original_capture','repeat_capture'):
            if not re.fullmatch('[0-9a-f]{64}', getattr(self,k)):
                raise ValueError('invalid capture digest')

    def packet(self):
        return asdict(self)


@dataclass(frozen=True)
class Policy:
    version: str
    tolerance: int
    require_question_match: bool = True
    require_selection_match: bool = True
    require_distinct_roots: bool = True

    def __post_init__(self):
        if not re.fullmatch(r'[A-Za-z0-9._-]{1,48}',self.version):
            raise ValueError('invalid policy version')
        if type(self.tolerance) is not int or not 0 <= self.tolerance <= 10000:
            raise ValueError('invalid tolerance')
        for field in ('require_question_match','require_selection_match','require_distinct_roots'):
            if type(getattr(self,field)) is not bool:
                raise ValueError('invalid policy flag')

    def packet(self):
        return asdict(self)


def evaluate(evidence: Evidence, policy: Policy):
    failures=[]
    if policy.require_question_match and not evidence.same_question:
        failures.append('QUESTION_DRIFT')
    if policy.require_selection_match and not evidence.same_selection:
        failures.append('SELECTION_DRIFT')
    if policy.require_distinct_roots and not evidence.distinct_declared_roots:
        failures.append('SHARED_ANCESTRY')
    delta=abs(evidence.original_value-evidence.repeated_value)
    if delta > policy.tolerance:
        failures.append('OUTSIDE_TOLERANCE')
    return {
        'policy_version':policy.version,
        'policy_digest':digest(policy.packet()),
        'evidence_digest':digest(evidence.packet()),
        'delta':delta,
        'failures':failures,
        'verdict':'DECLARED_FIXTURE_MATCH' if not failures else 'REJECTED',
        'scope':'declared synthetic evidence; not physical reproduction',
    }


class Audit:
    """Append-only in-process audit. External held head needed to detect truncation."""
    def __init__(self, evidence: Evidence, old: Policy, new: Policy):
        if old.version==new.version and old.packet()!=new.packet():
            raise ValueError('policy identity reused with different rules')
        self.evidence=evidence
        self.old=old
        self.new=new
        self.events=[]
        self.active_parent='FROZEN'
        self._append('EVIDENCE_FROZEN',{'digest':digest(evidence.packet()),'evidence':evidence.packet()})
        self._append('POLICY_FROZEN',{'version':old.version,'digest':digest(old.packet()),'rules':old.packet()})
        if old.packet()!=new.packet():
            self._append('POLICY_FROZEN',{'version':new.version,'digest':digest(new.packet()),'rules':new.packet()})

    def _append(self,kind,payload):
        body={'seq':len(self.events),'kind':kind,'payload':payload,
              'prev':self.events[-1]['hash'] if self.events else '0'*64}
        event={**body,'hash':digest(body)}
        self.events.append(event)
        return event

    def run(self):
        first=evaluate(self.evidence,self.old)
        second=evaluate(self.evidence,self.new)
        for output in (first,second):
            self._append('VERDICT',{'verdict_digest':digest(output),'verdict':output})
        policy_changed=first['policy_digest']!=second['policy_digest']
        verdict_changed=(first['verdict'],first['failures'])!=(second['verdict'],second['failures'])
        result={
            'experiment':'JANE-176',
            'invariant':'unchanged evidence != unchanged interpretation',
            'evidence_digest':first['evidence_digest'],
            'old':first,'new':second,
            'policy_changed':policy_changed,
            'verdict_changed':verdict_changed,
            'status':('POLICY_INDUCED_VERDICT_CHANGE' if policy_changed and verdict_changed
                      else 'POLICY_CHANGED_VERDICT_STABLE' if policy_changed
                      else 'POLICY_UNCHANGED'),
            'active_parent':self.active_parent,'learning_applied':False,
            'witness_independence_verified':False,
        }
        result['result_digest']=digest(result)
        self._append('REPLAY_RESULT',{'result_digest':result['result_digest'],'status':result['status']})
        return result

    def verify_ledger(self,expected_head=None):
        prior='0'*64
        for seq,item in enumerate(self.events):
            body={k:v for k,v in item.items() if k!='hash'}
            if item['seq']!=seq or item['prev']!=prior or item['hash']!=digest(body):
                return 'LEDGER_TAMPERED'
            prior=item['hash']
        if expected_head is not None and expected_head!=prior:
            return 'EXTERNAL_HEAD_MISMATCH'
        return 'VALID_LOCAL_CHAIN'


def fixture():
    evidence=Evidence(1000,1003,True,True,True,'a'*64,'b'*64)
    audit=Audit(evidence,Policy('v1',5),Policy('v2',2))
    result=audit.run()
    return audit,result


if __name__=='__main__':
    audit,result=fixture()
    print(json.dumps({'result':result,'ledger_verification':audit.verify_ledger(),
                      'ledger_head':audit.events[-1]['hash']},indent=2))