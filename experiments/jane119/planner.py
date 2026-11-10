"""JANE 119: bounded value-of-information planner (offline, no web fetching)."""
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json

@dataclass(frozen=True)
class Probe:
    key: str
    cost: int
    probability_change: Fraction
    benefit_if_changed: int
    confidence: Fraction = Fraction(1)
    visibility: str = 'public'
    origin: str = ''

    def score(self):
        if self.cost <= 0 or self.benefit_if_changed < 0:
            raise ValueError('Invalid cost or benefit')
        if not (0 <= self.probability_change <= 1 and 0 <= self.confidence <= 1):
            raise ValueError('Invalid probability or confidence')
        return self.probability_change * self.benefit_if_changed * self.confidence

def plan(probes, budget, max_probes=8):
    if budget < 0 or max_probes < 0:
        raise ValueError('Negative budget')
    candidates = tuple(probes)
    if len(candidates) > 128:
        raise ValueError('Too many candidates')
    if len({p.key for p in candidates}) != len(candidates):
        raise ValueError('Duplicate probe ID')
    for p in candidates:
        p.score()
    eligible = [p for p in candidates if p.visibility == 'public' and p.origin]
    eligible.sort(key=lambda p:p.key)
    if budget > 256 or max_probes > 32:
        raise ValueError('Budget exceeds fixed upper limit')
    dp = {(0,0): (Fraction(0), ())}
    for p in eligible:
        nxt = dict(dp)
        for (used,n), (v,ids) in dp.items():
            k=(used+p.cost,n+1)
            if k[0]>budget or k[1]>max_probes: continue
            cand=(v+p.score(),ids+(p.key,))
            incumbent=nxt.get(k)
            if incumbent is None or cand[0]>incumbent[0] or (cand[0]==incumbent[0] and cand[1]<incumbent[1]):
                nxt[k]=cand
        dp=nxt
    best=max(dp.items(),key=lambda item:(item[1][0],-item[0][0],-item[0][1],tuple(-ord(c) for c in '|'.join(item[1][1]))))
    (spent,count),(value,selected)=best
    return {'version':'JANE-119','selected':list(selected),'budget':budget,
            'spent':spent,'expected_value':str(value),'status':'PROPOSE_TO_JANE' if selected else 'ABSTAIN',
            'decision':'UNDECIDED','learning_applied':False,
            'excluded':[p.key for p in candidates if p not in eligible],
            'caveat':'Expected values are supplied assumptions, not empirical probabilities.'}

def audit_packet(packet):
    data=json.dumps(packet,sort_keys=True,separators=(',',':')).encode()
    return {'packet':packet,'sha256':hashlib.sha256(data).hexdigest()}

if __name__=='__main__':
    samples=[
      Probe('check_shared_parent',2,Fraction(4,5),10,origin='public-doc-a'),
      Probe('retrieve_duplicate_page',1,Fraction(0),100,origin='public-doc-a'),
      Probe('trace_unknown_branch',3,Fraction(1,2),12,origin='public-doc-b'),
      Probe('gated_material',1,Fraction(1),100,visibility='gated',origin='private'),
    ]
    print(json.dumps(audit_packet(plan(samples,4)),indent=2))
