"""JANE 197: bounded MNAR sensitivity, exact rational arithmetic.

Missing outcome assumptions are parameters, NEVER imputed observations.
"""
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json

def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'))
def sha(x): return sha256(canonical(x).encode()).hexdigest()
def fmt(x): return {"numerator":x.numerator,"denominator":x.denominator,"percentage":round(100*float(x),6)}

@dataclass(frozen=True)
class Stratum:
    name:str
    population:int
    observed:int
    successes:int
    ancestry:str
    def __post_init__(self):
        if not self.name or not self.ancestry or not all(type(v) is int for v in (self.population,self.observed,self.successes)):
            raise ValueError('invalid stratum fields')
        if not (0<self.population<=100000 and 0<=self.successes<=self.observed<=self.population):
            raise ValueError('invalid counts')
    @property
    def missing(self):return self.population-self.observed
    @property
    def rate(self):return None if not self.observed else Fraction(self.successes,self.observed)

@dataclass(frozen=True)
class Assumption:
    """delta: missing success probability minus observed rate; bounds clipped to [0,1].

    If no observed outcomes, delta is undefined. Require explicit [0,1] instead.
    """
    label:str
    deltas:tuple
    def __post_init__(self):
        if not self.label or not isinstance(self.deltas,tuple) or not all(isinstance(x,Fraction) and -1<=x<=1 for x in self.deltas):
            raise ValueError('bad sensitivity assumption')

class Audit:
    def __init__(self, strata, expected_ancestry_roots=None):
        self.strata=tuple(strata)
        if not self.strata or len(self.strata)>32 or len({s.name for s in strata})!=len(strata):raise ValueError('invalid population strata')
        self.population=sum(s.population for s in strata)
        self.frozen_digest=sha([s.__dict__ for s in self.strata]);self.parent='frozen';self.events=[]
        self.append('FREEZE',{'evidence_digest':self.frozen_digest,'population':self.population})
        self.ancestry_warning=len({s.ancestry for s in strata})<len(strata)
    def append(self,kind,data):
        e={'seq':len(self.events),'kind':kind,'data':data,'previous':self.events[-1]['hash'] if self.events else '0'*64}
        e['hash']=sha(e);self.events.append(e)
    def audit_chain(self,external_head=None):
        prev='0'*64
        for i,e in enumerate(self.events):
            if i!=e['seq'] or prev!=e['previous'] or e['hash']!=sha({k:v for k,v in e.items() if k!='hash'}):return 'TAMPERED'
            prev=e['hash']
        return 'EXTERNAL_HEAD_MISMATCH' if external_head is not None and external_head!=prev else 'VALID_LOCAL_CHAIN'
    def bounds(self):
        successes=sum(s.successes for s in self.strata)
        missing=sum(s.missing for s in self.strata)
        return {'lower':fmt(Fraction(successes,self.population)), 'upper':fmt(Fraction(successes+missing,self.population)),'missing':missing}
    def evaluate(self,assumption):
        if len(assumption.deltas)!=len(self.strata):raise ValueError('mismatched assumption')
        numerator=Fraction(0);rows=[];identifiable=True
        for s,delta in zip(self.strata,assumption.deltas):
            rate=s.rate
            if rate is None and s.missing:
                identifiable=False;rows.append({'name':s.name,'outcome':'UNOBSERVED_STRATUM','population':s.population,'missing':s.missing});continue
            missing_rate=max(Fraction(0),min(Fraction(1),rate+delta)) if rate is not None else Fraction(0)
            numerator+=s.successes+s.missing*missing_rate
            rows.append({'name':s.name,'observed_rate':fmt(rate) if rate is not None else None,
                         'assumed_missing_rate':fmt(missing_rate) if s.missing else None,
                         'missing':s.missing,'delta':fmt(delta)})
        result={'version':'JANE-197','status':'MNAR_SCENARIO_CONDITIONAL' if identifiable else 'UNIDENTIFIED_STRATUM',
                'assumption':assumption.label,'evidence_digest':self.frozen_digest,'population':self.population,
                'bounds':self.bounds(),'estimate':fmt(numerator/self.population) if identifiable else None,
                'strata':rows,'ancestry_warning':self.ancestry_warning,
                'inference_scope':'scenario conditional on unobserved-outcome assumptions; not observed truth',
                'active_parent':'frozen','learning_applied':False,'independent_witness_increment':0}
        result['digest']=sha(result)
        self.append('SCENARIO',{'digest':result['digest'],'assumption':assumption.label})
        return result

def demo():
    a=Audit([Stratum('day',8,6,5,'instrument-day'),Stratum('night',8,2,0,'instrument-night')])
    scenarios=[]
    for label,ds in [('equal-within-stratum',(Fraction(0),Fraction(0))),
                     ('missing-less-likely',(Fraction(-1,4),Fraction(-1,4))),
                     ('missing-more-likely',(Fraction(1,4),Fraction(1,4))),
                     ('extreme-low',(Fraction(-1),Fraction(-1))),
                     ('extreme-high',(Fraction(1),Fraction(1)))]:
        scenarios.append(a.evaluate(Assumption(label,ds)))
    return a,{'experiment':'JANE-197','scenarios':scenarios,'audit':a.audit_chain(),
              'scenario_count':len(scenarios),'tests':'run test_sensitivity.py'}
if __name__=='__main__':print(json.dumps(demo()[1],indent=2))