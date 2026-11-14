"""JANE 175: evidence-carrying comparison of declared experimental protocols.

Equality is exact on semantic and selection fields; instrumental equivalence is
only established through a *configured* equivalence class (never inferred).
"""
import hashlib
import json
from dataclasses import dataclass, asdict
from fractions import Fraction

SCHEMA = 'JANE-175/1'

def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True)

def sha(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()

@dataclass(frozen=True)
class Protocol:
    question: str
    estimand: str
    unit: str
    population: str
    sampling_frame: str
    inclusion: str
    exclusion: str
    selection_rule: str
    assignment: str
    instrument: str
    condition: str
    calibration: str
    processing: str
    aggregation: str
    time_window: str
    source_root: str
    raw_commitment: str
    def __post_init__(self):
        for name,value in asdict(self).items():
            if not isinstance(value,str) or not value.strip() or len(value)>512:
                raise ValueError('invalid '+name)
        if len(self.raw_commitment)!=64 or any(x not in '0123456789abcdef' for x in self.raw_commitment):
            raise ValueError('raw commitment must be sha256')

# Equality is evaluated by dimension, with no automatic coercion of terms.
DIMENSIONS={
 'question':['question','estimand','unit'],
 'sampling':['population','sampling_frame','inclusion','exclusion','selection_rule','assignment'],
 'instrument':['instrument','condition','calibration'],
 'analysis':['processing','aggregation'],
 'timing':['time_window'],
}

class Ledger:
    def __init__(self): self.events=[]
    def append(self,kind,data):
        prev=self.events[-1]['hash'] if self.events else '0'*64
        entry={'seq':len(self.events),'previous':prev,'kind':kind,'data':data}
        entry['hash']=sha(entry);self.events.append(entry)
        return entry['hash']
    def audit(self,external_head=None):
        previous='0'*64
        for i,e in enumerate(self.events):
            if e['seq']!=i or e['previous']!=previous or sha({k:v for k,v in e.items() if k!='hash'})!=e['hash']:
                return 'TAMPERED'
            previous=e['hash']
        if external_head is not None and external_head!=previous:return 'EXTERNAL_HEAD_MISMATCH'
        return 'VALID_LOCAL_CHAIN'

def compare(original,repeat,original_value,repeat_value,tolerance=Fraction(0),
            independent_roots=None, allowed_instrument_pairs=frozenset()):
    """Compares declared protocols; allowed instrument equivalence pairs are explicit policy.

    Every difference is preserved, including independently configured equivalences.
    source_root and raw_commitment are provenance, not equality of protocols.
    """
    if not isinstance(original,Protocol) or not isinstance(repeat,Protocol): raise TypeError('protocol')
    if any(not isinstance(v,(int,Fraction)) or isinstance(v,bool) for v in (original_value,repeat_value,tolerance)):
        raise TypeError('exact numeric evidence required')
    if tolerance<0:raise ValueError('negative tolerance')
    ledger=Ledger()
    ledger.append('FREEZE_ORIGINAL',{'protocol':asdict(original),'digest':sha(asdict(original)),'value':str(original_value)})
    ledger.append('CAPTURE_REPEAT',{'protocol':asdict(repeat),'digest':sha(asdict(repeat)),'value':str(repeat_value)})
    deviations=[];accepted_equivalences=[]
    for group,fields in DIMENSIONS.items():
        for name in fields:
            a,b=getattr(original,name),getattr(repeat,name)
            if a!=b:
                if name=='instrument' and (a,b) in allowed_instrument_pairs:
                    accepted_equivalences.append({'field':name,'from':a,'to':b,'basis':'configured equivalence policy'})
                else: deviations.append({'dimension':group,'field':name,'original':a,'repeat':b})
    # Always reveal shared source ancestry: identity of operator keys cannot remove it.
    ancestry_overlap= original.source_root==repeat.source_root
    if independent_roots is not None:
        if not (isinstance(independent_roots,(set,frozenset)) and
                original.source_root in independent_roots and repeat.source_root in independent_roots):
            raise ValueError('invalid declared roots')
    independent_declared=(not ancestry_overlap and independent_roots is not None)
    difference=abs(Fraction(original_value)-Fraction(repeat_value))
    matching=difference<=tolerance
    if deviations: status='PROTOCOL_DRIFT'
    elif not matching: status='RESULT_DISAGREEMENT'
    elif ancestry_overlap: status='SHARED_ACQUISITION_ANCESTRY'
    elif not independent_declared: status='INDEPENDENCE_UNESTABLISHED'
    else: status='DECLARED_FIXTURE_REPRODUCTION'
    result={
      'schema':SCHEMA,'status':status,'matching_numbers':matching,
      'protocol_equivalent_under_declared_policy':not deviations,
      'declared_root_distinct':not ancestry_overlap,
      'declared_independent_fixture_roots':independent_declared,
      'differences':deviations,'explicit_equivalences':accepted_equivalences,
      'original_hash':sha(asdict(original)),'repeat_hash':sha(asdict(repeat)),
      'raw_commitments_match':original.raw_commitment==repeat.raw_commitment,
      'absolute_value_difference':str(difference),'tolerance':str(tolerance),
      'physical_independence_verified':False,'active_parent':'FROZEN',
      'jane_activation':False,'scope':'declared protocol and synthetic fixture only'
    }
    result['digest']=sha(result)
    ledger.append('AUDIT',{'digest':result['digest'],'status':status,'differences':deviations,
                           'equivalences':accepted_equivalences})
    return result,ledger

def fixture(**changes):
    p=dict(question='clock oscillator accuracy',estimand='mean offset',unit='millisecond',
      population='oscillators generation 1',sampling_frame='all devices',
      inclusion='all devices',exclusion='none',selection_rule='uniform sample',
      assignment='deterministic seed 7',instrument='sensor-A',condition='20 C',
      calibration='reference-v1',processing='fixed point',aggregation='arithmetic mean',
      time_window='UTC 2026-11-14',source_root='acquisition-root-A',raw_commitment='a'*64)
    p.update(changes)
    return Protocol(**p)

def demo():
    original=fixture()
    repeated=fixture(source_root='acquisition-root-B',raw_commitment='b'*64)
    ok,_=compare(original,repeated,1000,1000,Fraction(2),{'acquisition-root-A','acquisition-root-B'})
    drift,_=compare(original,fixture(source_root='acquisition-root-B',raw_commitment='b'*64, selection_rule='select favorable responders'),1000,1000,Fraction(2),{'acquisition-root-A','acquisition-root-B'})
    shared,_=compare(original,fixture(raw_commitment='b'*64),1000,1000,Fraction(2),{'acquisition-root-A'})
    return {'version':SCHEMA,'cases':{'equivalent_fixture':ok,'matching_but_biased':drift,'shared_root':shared},'test_fixture_only':True}

if __name__=='__main__':print(json.dumps(demo(),indent=2))
