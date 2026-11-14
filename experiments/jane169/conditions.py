"""JANE 169: conservative clock uncertainty across operating-condition changes.

Offline deterministic fixture; condition labels are assertions, not measurements.
"""
from dataclasses import dataclass, asdict
from hashlib import sha256
import json


def canonical(x): return json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False)
def digest(x): return sha256(canonical(x).encode()).hexdigest()

@dataclass(frozen=True)
class Condition:
    temperature: str
    power: str
    sync: str
    def __post_init__(self):
        for field in (self.temperature,self.power,self.sync):
            if type(field) is not str or not field or len(field)>32:
                raise ValueError('invalid condition')
    def key(self): return f'{self.temperature}|{self.power}|{self.sync}'

@dataclass(frozen=True)
class Policy:
    ppm: int
    max_age_ms: int
    max_uncertainty_ms: int
    def __post_init__(self):
        if any(type(v) is not int or v<0 for v in (self.ppm,self.max_age_ms,self.max_uncertainty_ms)):
            raise ValueError('bad policy')
        if self.ppm>100000 or self.max_age_ms>10**10 or self.max_uncertainty_ms>10**9:
            raise ValueError('excessive policy')

@dataclass(frozen=True)
class Reading:
    tick_ms: int
    offset_ms: int
    condition: Condition
    def __post_init__(self):
        if type(self.tick_ms) is not int or self.tick_ms<0 or type(self.offset_ms) is not int:
            raise ValueError('invalid reading')


def growth(ppm, elapsed_ms):
    if elapsed_ms<0: raise ValueError('time reversal')
    return (ppm*elapsed_ms+999999)//1000000

class Monitor:
    def __init__(self, policies, baseline, initial_uncertainty_ms=2, external_head=None):
        if not isinstance(policies,dict) or not policies or not all(isinstance(k,str) and isinstance(v,Policy) for k,v in policies.items()):
            raise ValueError('invalid policy map')
        if baseline.condition.key() not in policies: raise ValueError('uncalibrated baseline')
        if type(initial_uncertainty_ms) is not int or initial_uncertainty_ms<0: raise ValueError('invalid uncertainty')
        self.policies=dict(policies)
        self.baseline=baseline
        self.last=baseline
        self.uncertainty=initial_uncertainty_ms
        self.age_origin=baseline.tick_ms
        self.current=baseline.condition.key()
        self.records=[]
        self.active='FROZEN_PARENT'
        self.external_head=external_head
        self._append('CALIBRATION', {'reading':asdict(baseline),'uncertainty_ms':initial_uncertainty_ms,'policy':asdict(policies[self.current])})

    def _append(self,kind,data):
        event={'seq':len(self.records),'kind':kind,'data':data,'prev':self.records[-1]['hash'] if self.records else '0'*64}
        event['hash']=digest(event)
        self.records.append(event)
        return event['hash']

    def observe(self,reading):
        if not isinstance(reading,Reading): raise ValueError('expected reading')
        prior=self.last
        if reading.tick_ms<=prior.tick_ms:
            outcome={'status':'NONMONOTONIC_TIME','accepted':False,'uncertainty_ms':self.uncertainty}
            self._append('REJECT',dict(reading=asdict(reading),outcome=outcome))
            return outcome
        elapsed=reading.tick_ms-prior.tick_ms
        old_policy=self.policies.get(self.current)
        if old_policy is None:
            outcome={'status':'RECALIBRATION_REQUIRED','accepted':False,'uncertainty_ms':None,'condition_changed':reading.condition.key()!=self.current,'recalibration_required':True}
            self.last=reading
            self._append('HOLD',dict(reading=asdict(reading),outcome=outcome))
            return outcome
        old_growth=growth(old_policy.ppm,elapsed)
        carried=self.uncertainty+old_growth
        changed=reading.condition.key()!=self.current
        new_policy=self.policies.get(reading.condition.key())
        offset_change=abs(reading.offset_ms-prior.offset_ms)
        if changed and new_policy is None:
            outcome={'status':'UNKNOWN_CONDITION','accepted':False,'uncertainty_ms':None,'last_bounded_uncertainty_ms':carried,'condition_changed':True,'recalibration_required':True}
            self.uncertainty=carried
            self.last=reading  # time advances; no new assumed calibration bound
            self.current=reading.condition.key()
            self._append('HOLD',dict(reading=asdict(reading),outcome=outcome))
            return outcome
        # A transition's actual time is unknown: charge the greater drift rate across the ENTIRE interval.
        if changed:
            carried=self.uncertainty+growth(max(old_policy.ppm,new_policy.ppm),elapsed)
        new_age=reading.tick_ms-self.age_origin
        if offset_change>carried:
            status='CLOCK_JUMP'
        elif new_age>new_policy.max_age_ms or carried>new_policy.max_uncertainty_ms:
            status='CALIBRATION_EXPIRED'
        else:
            status='CONDITION_CHANGE_ACCEPTED' if changed else 'WITHIN_PROFILE'
        outcome={'status':status,'accepted':status in ('WITHIN_PROFILE','CONDITION_CHANGE_ACCEPTED'), 'uncertainty_ms':carried,'condition_changed':changed,'recalibration_required':status in ('CLOCK_JUMP','CALIBRATION_EXPIRED')}
        self._append('OBSERVE' if outcome['accepted'] else 'HOLD',dict(reading=asdict(reading),outcome=outcome))
        # Rejected jump/expiry must not become a trusted new calibration baseline.
        if outcome['accepted']:
            self.last=reading
            self.current=reading.condition.key()
            self.uncertainty=carried
        return outcome

    def calibrate(self,reading,verified_uncertainty_ms,reference_digest):
        if not isinstance(reading,Reading) or type(verified_uncertainty_ms) is not int or verified_uncertainty_ms<0:
            raise ValueError('bad calibration')
        if reading.condition.key() not in self.policies: raise ValueError('unknown condition')
        if len(reference_digest)!=64 or any(c not in '0123456789abcdef' for c in reference_digest): raise ValueError('missing calibration evidence digest')
        if reading.tick_ms<self.last.tick_ms: raise ValueError('calibration predates last observed tick')
        self.baseline=reading;self.last=reading;self.age_origin=reading.tick_ms
        self.uncertainty=verified_uncertainty_ms;self.current=reading.condition.key()
        self._append('RECALIBRATE',dict(reading=asdict(reading),verified_uncertainty_ms=verified_uncertainty_ms,reference_digest=reference_digest))
        return 'RECALIBRATED_WITH_DECLARED_EVIDENCE'

    def audit(self,external_head=None):
        prev='0'*64
        for seq,e in enumerate(self.records):
            if e['seq']!=seq or e['prev']!=prev or e['hash']!=digest({k:v for k,v in e.items() if k!='hash'}): return 'TAMPERED'
            prev=e['hash']
        anchor=external_head if external_head is not None else self.external_head
        return 'EXTERNAL_HEAD_MISMATCH' if anchor and anchor!=prev else 'VALID_LOCAL_CHAIN'


def demo():
    normal=Condition('normal','mains','locked')
    hot=Condition('hot','battery','holdover')
    unknown=Condition('unknown','battery','holdover')
    policies={normal.key():Policy(20,60000,100),hot.key():Policy(100,60000,100)}
    a=Monitor(policies,Reading(0,0,normal),2)
    stable=a.observe(Reading(10000,1,normal))
    changed=a.observe(Reading(20000,2,hot))
    jump=a.observe(Reading(21000,50,hot))
    b=Monitor(policies,Reading(0,0,normal),2)
    missing=b.observe(Reading(10000,1,unknown))
    return {'version':'JANE-169','stable':stable,'changed':changed,'jump':jump,'unknown_profile':missing,'audit':a.audit(),'active':a.active,'proof_scope':'declared deterministic condition labels and bounds only','real_clock_authenticated':False,'learning_applied':False}

if __name__=='__main__': print(json.dumps(demo(),indent=2))