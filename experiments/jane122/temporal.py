"""JANE 122: temporal drift evaluator; offline, append-only-style evidence."""
from dataclasses import dataclass
from hashlib import sha256
import json
@dataclass(frozen=True)
class Observation:
    case_id: str
    cohort: str
    time: int
    truth: bool
    old_prediction: bool|None
    new_prediction: bool|None
    origin: str
@dataclass(frozen=True)
class Freeze:
    version: str
    time: int
    rule_digest: str
    parent_digest: str|None=None
def fingerprint(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def freeze_rule(version,time,rule_text,parent=None):
    if not version or time<0 or not rule_text:raise ValueError('invalid freeze')
    return Freeze(version,time,fingerprint(rule_text),parent)
def assess(freeze,observations,min_matches=2):
    rows=tuple(observations)
    if len(rows)>256 or min_matches<1:raise ValueError('budget')
    keys=set()
    for r in rows:
        if not r.case_id or not r.cohort or not r.origin or r.time<freeze.time:raise ValueError('invalid evidence')
        k=(r.case_id,r.time)
        if k in keys:raise ValueError('duplicate')
        keys.add(k)
    times=sorted({r.time for r in rows})
    periods=[]
    for t in times:
        group=[r for r in rows if r.time==t]
        known=[r for r in group if r.old_prediction is not None and r.new_prediction is not None]
        old=sum(r.old_prediction==r.truth for r in known)
        new=sum(r.new_prediction==r.truth for r in known)
        periods.append(dict(time=t,eligible=len(known),old_correct=old,new_correct=new,
                            paired_gain=new-old,abstentions=len(group)-len(known),
                            cohorts=sorted({r.cohort for r in known})))
    latest=max((t for t in times if t>freeze.time),default=None)
    matched=[]
    if freeze.time not in times or latest is None:
        status='INSUFFICIENT_PERIODS'
    else:
        before={r.case_id:r for r in rows if r.time==freeze.time}
        after={r.case_id:r for r in rows if r.time==latest}
        matched=[(before[k],after[k]) for k in sorted(before.keys()&after.keys())
                 if before[k].cohort==after[k].cohort
                 and before[k].old_prediction is not None and after[k].old_prediction is not None
                 and before[k].new_prediction is not None and after[k].new_prediction is not None]
        if len(matched)<min_matches:status='INSUFFICIENT_MATCHED_CASES'
        else:
            prior=sum(a.new_prediction==a.truth for a,b in matched)
            later=sum(b.new_prediction==b.truth for a,b in matched)
            status='DRIFT_CANDIDATE' if later<prior else 'STABLE_ON_MATCHED_CASES'
    result=dict(version='JANE-122',freeze=freeze.__dict__,periods=periods,
                matched_count=len(matched),status=status,jane_decision='UNDECIDED',
                learning_applied=False,
                caveat='Matched observations do not prove causal drift; ancestry is declared.')
    result['digest']=fingerprint(result)
    return result
def demonstration():
    f=freeze_rule('ancestry-v1',0,'root-aware-v1')
    rows=[Observation('a','mirror',0,False,True,False,'owned'),
          Observation('b','wire',0,False,True,False,'wire'),
          Observation('c','labs',0,True,True,True,'labs'),
          Observation('a','mirror',1,False,True,False,'owned'),
          Observation('b','wire',1,True,True,False,'wire'),
          Observation('c','labs',1,True,True,True,'labs')]
    return assess(f,rows)
if __name__=='__main__':print(json.dumps(demonstration(),indent=2))
