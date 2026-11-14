"""JANE 199: proxy agreement is not evidence of latent-cause identification.

All data are synthetic. Unknown outcomes remain unknown in observed records.
"""
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)

def digest(value):
    return sha256(canonical(value).encode()).hexdigest()

def fraction(value):
    return {'numerator':value.numerator,'denominator':value.denominator,
            'percent':round(float(value)*100,5)}

@dataclass(frozen=True)
class Record:
    round_id:int
    group:str
    proxy:int
    selected:bool
    outcome:int|None
    def __post_init__(self):
        if type(self.round_id) is not int or self.round_id<0 or not self.group:
            raise ValueError('invalid identity')
        if type(self.proxy) is not int or self.proxy not in (0,1):
            raise ValueError('proxy must be binary')
        if type(self.selected) is not bool: raise ValueError('invalid selection')
        if self.selected and (type(self.outcome) is not int or self.outcome not in (0,1)):
            raise ValueError('selected record requires binary outcome')
        if not self.selected and self.outcome is not None:
            raise ValueError('unselected outcomes must stay unknown')

@dataclass(frozen=True)
class Model:
    name:str
    latent:tuple[int,...]
    ancestry:str
    def __post_init__(self):
        if not self.name or not self.ancestry or not self.latent:
            raise ValueError('invalid model identity')
        if any(type(x) is not int or x not in (0,1) for x in self.latent):
            raise ValueError('latent values must be binary')

@dataclass(frozen=True)
class Calibration:
    indices:tuple[int,...]
    root:str
    upstream:str
    def __post_init__(self):
        if not self.root or not self.upstream or not self.indices:
            raise ValueError('invalid calibration')
        if any(type(i) is not int or i<0 for i in self.indices) or len(set(self.indices))!=len(self.indices):
            raise ValueError('invalid validation indices')

class FLAY199:
    def __init__(self,records):
        records=tuple(records)
        if not records or len(records)>10000 or not all(isinstance(r,Record) for r in records):
            raise ValueError('invalid records')
        if len({r.round_id for r in records})!=len(records): raise ValueError('duplicate round')
        self.rows=tuple(sorted(records,key=lambda r:r.round_id))
        self.frozen=digest([r.__dict__ for r in self.rows])
        self.history=[]
        self._append('FROZEN',{'digest':self.frozen})

    def _append(self,kind,body):
        ev={'sequence':len(self.history),'kind':kind,'body':body,
            'previous':self.history[-1]['hash'] if self.history else '0'*64}
        ev['hash']=digest(ev)
        self.history.append(ev)

    def chain_status(self):
        prev='0'*64
        for i,ev in enumerate(self.history):
            if ev.get('sequence')!=i or ev.get('previous')!=prev or ev.get('hash')!=digest({k:v for k,v in ev.items() if k!='hash'}):
                return 'TAMPERED'
            prev=ev['hash']
        return 'VALID_LOCAL_CHAIN'

    def evaluate(self,models,calibration=None):
        models=tuple(models)
        if not models or len(models)>32 or any(not isinstance(m,Model) for m in models):
            raise ValueError('invalid model set')
        if len({m.name for m in models})!=len(models): raise ValueError('duplicate model')
        if calibration is not None and not isinstance(calibration,Calibration):
            raise ValueError('invalid calibration type')
        if calibration is not None and any(i>=len(self.rows) for i in calibration.indices):
            raise ValueError('calibration index out of bounds')
        if calibration is not None and any(not self.rows[i].selected for i in calibration.indices):
            raise ValueError('calibration requires independently known outcome')
        n=len(self.rows)
        successes=sum(r.outcome for r in self.rows if r.selected)
        missing=sum(not r.selected for r in self.rows)
        candidates=[]
        for m in models:
            if len(m.latent)!=n: raise ValueError('model size mismatch')
            compatible=all(not r.selected or r.outcome==m.latent[i] for i,r in enumerate(self.rows))
            calibration_agrees=(None if calibration is None else all(m.latent[i]==self.rows[i].outcome for i in calibration.indices))
            observed_correct=sum(r.proxy==m.latent[i] for i,r in enumerate(self.rows) if r.selected)
            missing_correct=sum(r.proxy==m.latent[i] for i,r in enumerate(self.rows) if not r.selected)
            candidates.append({'name':m.name,'compatible':compatible,
              'candidate_rate':fraction(Fraction(sum(m.latent),n)),
              'observed_proxy_accuracy':fraction(Fraction(observed_correct,n-missing)),
              'unobserved_proxy_accuracy_HYPOTHETICAL':fraction(Fraction(missing_correct,missing)) if missing else None,
              'calibration_agrees':calibration_agrees,'ancestry':m.ancestry,
              'candidate_digest':digest({'name':m.name,'latent':m.latent,'ancestry':m.ancestry})})
        valid=[c for c in candidates if c['compatible'] and c['calibration_agrees'] is not False]
        rates={(c['candidate_rate']['numerator'],c['candidate_rate']['denominator']) for c in valid}
        if len(valid)>=2 and len(rates)>1: verdict='PROXY_CAUSAL_NONIDENTIFIABILITY'
        elif not valid: verdict='NO_COMPATIBLE_PROXY_MODEL'
        elif len(valid)>1: verdict='MULTIPLE_MODELS_SAME_RATE'
        else: verdict='SINGLE_COMPATIBLE_MODEL_NOT_IDENTIFIED'
        calib={'rows':len(calibration.indices),'root':calibration.root,'upstream':calibration.upstream,
               'coverage':'SELECTED_ONLY','independent_custody_verified':False} if calibration else None
        result={'experiment':'JANE-199','verdict':verdict,'frozen_digest':self.frozen,
                'population':n,'selected':n-missing,'missing':missing,'proxy_recorded':n,
                'observed_successes':successes,
                'assumption_free_bounds':{'lower':fraction(Fraction(successes,n)),
                                          'upper':fraction(Fraction(successes+missing,n))},
                'calibration':calib,'candidates':candidates,
                'causal_identified':False,'parent':'FROZEN','learning_applied':False,
                'warning':'Proxy accuracy on observed records does not validate proxy errors on missing records. Synthetic fixtures only.'}
        result['digest']=digest(result)
        self._append('COMPARE',{'verdict':verdict,'result_digest':result['digest']})
        return result


def fixture():
    rows=tuple(Record(i,'DAY' if i<8 else 'NIGHT',
                       1 if i in (0,1,2,3,4) else 0,
                       i in (0,1,2,3,4,5,8,9),
                       1 if i in (0,1,2,3,4) else 0 if i in (5,8,9) else None)
               for i in range(16))
    a=Model('A_proxy_reliable',tuple(r.outcome if r.selected else 0 for r in rows),'synthetic-root-A')
    b=Model('B_proxy_misleading',tuple(r.outcome if r.selected else 1 for r in rows),'synthetic-root-B')
    return rows,(a,b),Calibration((0,1,2,3,4,5,8,9),'synthetic-calibration','shared-observed-corpus')

if __name__=='__main__':
    rows,models,calibration=fixture()
    flay=FLAY199(rows)
    print(json.dumps({'result':flay.evaluate(models,calibration),'audit_status':flay.chain_status()},indent=2))