"""JANE 196: transparent stratified estimands and assumption-limited bounds.

All outcomes are binary; no missing-at-random inference is silently performed.
"""
from dataclasses import dataclass
from fractions import Fraction
import hashlib, json

def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(',',':'))
def sha(obj): return hashlib.sha256(canonical(obj).encode()).hexdigest()

@dataclass(frozen=True)
class Stratum:
    label:str
    population:int
    sampled:int
    observed_ones:int
    observed_zeros:int
    provenance_roots:tuple=()
    def __post_init__(self):
        if not self.label or not all(type(x) is int for x in (self.population,self.sampled,self.observed_ones,self.observed_zeros)):
            raise ValueError('invalid stratum')
        if not (0 < self.population <= 100000 and 0 <= self.sampled <= self.population and 0 <= self.observed_ones <= self.sampled and 0 <= self.observed_zeros <= self.sampled and self.observed_ones+self.observed_zeros<=self.sampled):
            raise ValueError('invalid counts')
        if len(set(self.provenance_roots)) != len(self.provenance_roots):raise ValueError('duplicate ancestry root')
    @property
    def observed(self):return self.observed_ones+self.observed_zeros
    @property
    def unknown(self):return self.population-self.observed

def as_obj(f): return {'numerator':f.numerator,'denominator':f.denominator,'decimal':round(float(f),8)}

class Audit:
    def __init__(self,strata,required_roots=2,assumption='none'):
        if not strata or len(strata)>32 or len({s.label for s in strata})!=len(strata):raise ValueError('invalid strata')
        if type(required_roots) is not int or not 1<=required_roots<=10:raise ValueError('roots')
        if assumption not in ('none','within_stratum_exchangeability'):raise ValueError('assumption')
        self.strata=tuple(sorted(strata,key=lambda s:s.label));self.required_roots=required_roots;self.assumption=assumption
        self.events=[];self._append('FREEZE',{'strata':[s.__dict__ for s in self.strata],'assumption':assumption,'required_roots':required_roots})
    def _append(self,kind,data):
        e={'seq':len(self.events),'kind':kind,'data':data,'prev':self.events[-1]['head'] if self.events else '0'*64}
        e['head']=sha(e);self.events.append(e)
    def evaluate(self):
        N=sum(s.population for s in self.strata)
        lower=Fraction(sum(s.observed_ones for s in self.strata),N)
        upper=Fraction(sum(s.observed_ones+s.unknown for s in self.strata),N)
        rows=[];point=Fraction(0);missing=[];inadequate=[];shared=[]
        used=set()
        for s in self.strata:
            roots=set(s.provenance_roots)
            if len(roots)<self.required_roots:inadequate.append(s.label)
            if used.intersection(roots):shared.append(s.label)
            used.update(roots)
            if s.observed==0:missing.append(s.label)
            else:point+=Fraction(s.population,N)*Fraction(s.observed_ones,s.observed)
            rows.append({'label':s.label,'population':s.population,'sampled':s.sampled,'observed':s.observed,
                         'unobserved':s.unknown,'selection_fraction':as_obj(Fraction(s.sampled,s.population)),
                         'response_fraction':as_obj(Fraction(s.observed,s.sampled)) if s.sampled else None,
                         'observed_rate':as_obj(Fraction(s.observed_ones,s.observed)) if s.observed else None,
                         'declared_roots':sorted(roots),'independent_roots_established':False})
        # Complete observation is an arithmetic census; adjusted estimates otherwise require stated assumptions.
        complete=all(s.unknown==0 for s in self.strata)
        point_allowed=not missing and (complete or self.assumption=='within_stratum_exchangeability')
        status=('UNOBSERVED_STRATUM_NO_POINT' if missing else
                'BOUNDED_ONLY_NO_EXCHANGEABILITY' if not point_allowed else
                'COMPLETE_CENSUS' if complete else 'ASSUMPTION_CONDITIONAL_ESTIMATE')
        if inadequate or shared:status='ANCESTRY_LIMITED_'+status
        result={'version':'JANE-196','status':status,'total_population':N,'rows':rows,
                'population_outcome_bounds':{'lower':as_obj(lower),'upper':as_obj(upper)},
                'conditional_population_estimate':as_obj(point) if point_allowed else None,
                'point_estimate_assumption':('complete enumeration' if complete else self.assumption) if point_allowed else None,
                'unobserved_strata':missing,'insufficient_declared_ancestry':inadequate,
                'shared_ancestry_across_strata':shared,
                'scope':'finite declared population; binary outcomes; no physical source independence established',
                'active':'frozen_parent','jane_decision':'UNDECIDED','auto_learning':False,'independent_witness_increment':0}
        result['digest']=sha(result)
        self._append('EVALUATE',{'digest':result['digest'],'status':status})
        return result
    def verify_ledger(self,external_head=None):
        prev='0'*64
        for i,e in enumerate(self.events):
            if e['seq']!=i or e['prev']!=prev or e['head']!=sha({k:v for k,v in e.items() if k!='head'}):return 'TAMPERED'
            prev=e['head']
        return 'EXTERNAL_HEAD_MISMATCH' if external_head is not None and external_head!=prev else 'VALID_LOCAL_CHAIN'

def demo():
    # Imbalanced draw: day 6/8, night 2/8. 5 successes, 3 zeros observed.
    day=Stratum('day',8,6,5,1,('dayA','dayB'))
    night=Stratum('night',8,2,0,2,('nightA','nightB'))
    a=Audit((day,night),assumption='within_stratum_exchangeability')
    return a,a.evaluate()
if __name__=='__main__':
    a,result=demo(); print(json.dumps({'result':result,'audit':a.verify_ledger()},indent=2))
