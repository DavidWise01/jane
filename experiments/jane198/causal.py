"""JANE 198: construct observationally equivalent hidden-cause explanations.

A matching projection is a compatibility finding, NOT a causal inference.
All models and observations here are synthetic fixtures.
"""
from dataclasses import dataclass
from hashlib import sha256
from fractions import Fraction
import json

def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)

def digest(obj):
    return sha256(canon(obj).encode()).hexdigest()

def rational(x):
    return {'numerator':x.numerator,'denominator':x.denominator,'percentage':round(float(x)*100,6)}

@dataclass(frozen=True)
class Observation:
    round_id: int
    stratum: str
    selected: bool
    outcome: int | None
    def __post_init__(self):
        if type(self.round_id) is not int or self.round_id<0 or not self.stratum:
            raise ValueError('invalid round identity')
        if type(self.selected) is not bool:
            raise ValueError('invalid selection flag')
        if self.selected and (type(self.outcome) is not int or self.outcome not in (0,1)):
            raise ValueError('selected row needs binary outcome')
        if not self.selected and self.outcome is not None:
            raise ValueError('missing outcome must be None')

@dataclass(frozen=True)
class CausalCandidate:
    """Illustrative deterministic SCM: Y=U, R=1 iff U equals per-row gate.

    Gate is predeclared within each candidate; it is not observed evidence.
    This artificial SCM shows compatible distinct latent selection processes.
    """
    name: str
    latent: tuple[int,...]
    gates: tuple[int,...]
    ancestry: str
    def __post_init__(self):
        if not self.name or not self.ancestry or not self.latent or len(self.latent)!=len(self.gates):
            raise ValueError('invalid candidate')
        if any(type(x) is not int or x not in (0,1) for x in (*self.latent,*self.gates)):
            raise ValueError('latent and gates must be binary')
    def projection(self, identities):
        if len(identities)!=len(self.latent):
            raise ValueError('length mismatch')
        return tuple(Observation(r.round_id,r.stratum,self.latent[i]==self.gates[i],
                    self.latent[i] if self.latent[i]==self.gates[i] else None)
                    for i,r in enumerate(identities))
    def prevalence(self):
        return Fraction(sum(self.latent),len(self.latent))

class FLAY198:
    def __init__(self,observations):
        rows=tuple(observations)
        if not rows or len(rows)>10000 or len({r.round_id for r in rows})!=len(rows):
            raise ValueError('invalid population or repeated round')
        if not all(isinstance(r,Observation) for r in rows):
            raise ValueError('invalid observation')
        self.rows=tuple(sorted(rows,key=lambda r:r.round_id))
        self.frozen=digest([r.__dict__ for r in self.rows])
        self.events=[]
        self.append('FREEZE', {'observation_digest':self.frozen})
    def append(self,kind,data):
        item={'seq':len(self.events),'kind':kind,'data':data,
              'previous':self.events[-1]['hash'] if self.events else '0'*64}
        item['hash']=digest(item)
        self.events.append(item)
    def audit(self):
        head='0'*64
        for i,e in enumerate(self.events):
            if e['seq']!=i or e['previous']!=head or e['hash']!=digest({k:v for k,v in e.items() if k!='hash'}):
                return 'TAMPERED'
            head=e['hash']
        return 'VALID_LOCAL_CHAIN'
    def bounds(self):
        success=sum(r.outcome for r in self.rows if r.selected)
        unknown=sum(not r.selected for r in self.rows)
        n=len(self.rows)
        return {'lower':rational(Fraction(success,n)),'upper':rational(Fraction(success+unknown,n)),
                'observed_successes':success,'unknown_outcomes':unknown,'population':n}
    def compare(self, candidates):
        candidates=tuple(candidates)
        if not candidates or len(candidates)>32 or any(not isinstance(c,CausalCandidate) for c in candidates):
            raise ValueError('invalid candidate set')
        if len({c.name for c in candidates})!=len(candidates):
            raise ValueError('duplicate names')
        models=[]
        for c in candidates:
            projected=c.projection(self.rows)
            compatible=projected==self.rows
            models.append({'name':c.name,'compatible':compatible,
                           'projected_digest':digest([r.__dict__ for r in projected]),
                           'population_rate':rational(c.prevalence()),
                           'candidate_digest':digest({'name':c.name,'latent':c.latent,'gates':c.gates}),
                           'ancestry':c.ancestry})
        matched=[m for m in models if m['compatible']]
        distinct_rates={m['population_rate']['numerator'] / m['population_rate']['denominator'] for m in matched}
        verdict=('NONIDENTIFIABLE_COMPETING_MODELS' if len(matched)>=2 and len(distinct_rates)>=2
                 else 'MULTIPLE_COMPATIBLE_SAME_RATE' if len(matched)>=2
                 else 'SINGLE_COMPATIBLE_MODEL' if matched else 'NO_COMPATIBLE_MODEL')
        result={'experiment':'JANE-198','verdict':verdict,'frozen_observation_digest':self.frozen,
                'bounds':self.bounds(),'candidates':models,
                'compatible_count':len(matched),'causal_identification':False,
                'observer_roots_are_independent':False,'learning_applied':False,
                'active_parent':'frozen',
                'warning':'Candidate models and latent outcomes are constructed fixtures, not observed causes.'}
        result['digest']=digest(result)
        self.append('COMPARE',{'digest':result['digest'],'verdict':verdict})
        return result

def demo():
    # Day: six observed (five successes); night: two observed (zero successes).
    rows=tuple([Observation(i,'day' if i<8 else 'night',i in {0,1,2,3,4,5,8,9},
                            1 if i in {0,1,2,3,4} else 0 if i in {5,8,9} else None)
                for i in range(16)])
    observed=[r.outcome for r in rows]
    def candidate(name,missing):
        latent=tuple(observed[i] if observed[i] is not None else missing for i in range(16))
        gates=tuple(latent[i] if rows[i].selected else 1-latent[i] for i in range(16))
        return CausalCandidate(name,latent,gates,'synthetic-source-one')
    a=FLAY198(rows)
    result=a.compare((candidate('low-latent-success',0),candidate('high-latent-success',1)))
    return a, result

if __name__=='__main__':
    print(json.dumps(demo()[1],indent=2))