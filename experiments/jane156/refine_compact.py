"""JANE 156 repository reproduction: affine-interval invariant strengthening.
Full 41-test artifact is distributed separately in the tested ZIP.
"""
from dataclasses import dataclass
from hashlib import sha256
import json

def digest(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

@dataclass(frozen=True)
class Interval:
    low:int
    high:int|None=None
    def __post_init__(self):
        if type(self.low) is not int or (self.high is not None and type(self.high) is not int) or (self.high is not None and self.high<self.low):
            raise ValueError('invalid interval')
    def contains(self,s):return s>=self.low and (self.high is None or s<=self.high)

@dataclass(frozen=True)
class Affine:
    a:int
    b:int
    def __post_init__(self):
        if type(self.a) is not int or type(self.b) is not int:raise ValueError('integer coefficients')
    def apply(self,s):return self.a*s+self.b

def verify(region,transition,initial):
    if not region.contains(initial):return {'status':'INITIAL_OUTSIDE','witness':initial}
    a,b=transition.a,transition.b
    if region.high is None:
        if a<0:
            witness=max(region.low,(b-region.low)//(-a)+1)
            return {'status':'INDUCTIVE_FAILURE','witness':witness,'next':transition.apply(witness)}
        if transition.apply(region.low)<region.low:
            return {'status':'INDUCTIVE_FAILURE','witness':region.low,'next':transition.apply(region.low)}
        return {'status':'INDUCTIVE_PROVEN','method':'unbounded_affine_lower_bound'}
    for s in (region.low,region.high):
        if not region.contains(transition.apply(s)):
            return {'status':'INDUCTIVE_FAILURE','witness':s,'next':transition.apply(s)}
    return {'status':'INDUCTIVE_PROVEN','method':'affine_endpoint_extrema'}

def experiment():
    initial=0;transition=Affine(-1,20)
    original=Interval(0,None);failure=verify(original,transition,initial)
    # Restricted synthesis: candidate from slope -1 and required lower bound.
    upper=transition.b-original.low
    proposed=Interval(original.low,upper)
    checked=verify(proposed,transition,initial)
    events=[];prev='0'*64
    for kind,payload in [('FROZEN_PARENT',{'initial':initial,'transition':[-1,20]}),
                         ('PRESERVE_FAILURE',failure),
                         ('PROPOSE_REFINEMENT',{'region':[proposed.low,proposed.high],'check':checked})]:
        entry={'sequence':len(events),'previous':prev,'kind':kind,'payload':payload}
        entry['hash']=digest(entry);events.append(entry);prev=entry['hash']
    result={'version':'JANE-156','status':'REFINEMENT_PROVEN_IN_MODEL' if checked['status']=='INDUCTIVE_PROVEN' else 'REFINEMENT_REJECTED',
            'initial':initial,'original_failure':failure,'refined_region':[proposed.low,proposed.high],
            'proof':checked,'events':events,'head':prev,'parent':'FROZEN',
            'jane_decision':'UNDECIDED','learning_applied':False,
            'claim_scope':'declared affine integer model only'}
    result['digest']=digest(result)
    return result
if __name__=='__main__':print(json.dumps(experiment(),indent=2))
