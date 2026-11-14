"""JANE 168: conservative time-calibration drift auditing.

Local synthetic observations only. A signed clock claim is not proof of physical time.
All timestamps in integer milliseconds. Audit decisions never activate Jane.
"""
from dataclasses import dataclass, asdict
import hashlib, json, math

def canonical(x): return json.dumps(x, sort_keys=True, separators=(',',':'))
def hexdigest(x): return hashlib.sha256(canonical(x).encode()).hexdigest()

@dataclass(frozen=True)
class Policy:
    max_drift_ppm: int = 100
    max_age_ms: int = 30_000
    max_uncertainty_ms: int = 12
    jump_slack_ms: int = 3
    def __post_init__(self):
        vals=asdict(self)
        if any(type(v) is not int or v<0 or v>10**7 for v in vals.values()): raise ValueError('bad policy')

@dataclass(frozen=True)
class Observation:
    sequence: int
    reference_ms: int
    offset_ms: int
    uncertainty_ms: int
    source_root: str
    # Evidence binding: this is a claim / fixture identifier; signed provenance is upstream.
    evidence_hash: str
    def __post_init__(self):
        if any(type(v) is not int for v in (self.sequence,self.reference_ms,self.offset_ms,self.uncertainty_ms)):
            raise ValueError('noninteger')
        if self.sequence<0 or self.reference_ms<0 or self.uncertainty_ms<0 or self.uncertainty_ms>10**6: raise ValueError('range')
        if not self.source_root or not isinstance(self.source_root,str) or not isinstance(self.evidence_hash,str) or len(self.evidence_hash)!=64 or any(c not in '0123456789abcdef' for c in self.evidence_hash): raise ValueError('evidence')

@dataclass(frozen=True)
class Decision:
    status: str
    reason: str
    predicted_uncertainty_ms: int|None
    elapsed_ms: int|None
    observed_offset_change_ms: int|None

class DriftLedger:
    def __init__(self,policy:Policy,epoch:Observation):
        self.policy=policy;self.epoch=epoch;self.history=[epoch];self.log=[];self.active='frozen_parent'
        self._append('CALIBRATION_BASELINE',{'observation':asdict(epoch),'policy':asdict(policy)})
    def _append(self,kind,payload):
        record={'index':len(self.log),'kind':kind,'payload':payload,'prev':self.log[-1]['hash'] if self.log else '0'*64}
        record['hash']=hexdigest(record);self.log.append(record)
    def check(self,obs:Observation)->Decision:
        prev=self.history[-1]
        if obs.sequence<=prev.sequence: d=Decision('REPLAY_OR_REORDER','nonincreasing sequence',None,None,None)
        elif obs.reference_ms<=prev.reference_ms: d=Decision('CLOCK_REVERSAL','reference time not advancing',None,None,None)
        else:
            elapsed=obs.reference_ms-prev.reference_ms
            growth=math.ceil(elapsed*self.policy.max_drift_ppm/1_000_000)
            expected=prev.uncertainty_ms+growth
            change=abs(obs.offset_ms-prev.offset_ms)
            # Two interval estimates can legitimately disagree by their combined uncertainty.
            allowed=growth+prev.uncertainty_ms+obs.uncertainty_ms+self.policy.jump_slack_ms
            if elapsed>self.policy.max_age_ms: status,reason='CALIBRATION_EXPIRED','elapsed beyond calibration age'
            elif expected>self.policy.max_uncertainty_ms: status,reason='UNCERTAINTY_EXPIRED','uncertainty budget exhausted'
            elif change>allowed: status,reason='CLOCK_JUMP','offset change exceeds conservative drift envelope'
            else: status,reason='CALIBRATION_CONSISTENT_FIXTURE','observations consistent with declared envelope'
            d=Decision(status,reason,expected,elapsed,change)
        self._append('OBSERVED',{'observation':asdict(obs),'decision':asdict(d)})
        # Never let a suspicious or expired calibration silently become a new trusted epoch.
        # Retain observations, but advance only on successful checks.
        if d.status=='CALIBRATION_CONSISTENT_FIXTURE':self.history.append(obs)
        return d
    def forecast(self,now_ms:int)->Decision:
        if type(now_ms) is not int or now_ms<0:raise ValueError('invalid current time')
        base=self.history[-1]
        if now_ms<base.reference_ms:return Decision('CLOCK_REVERSAL','current time precedes reference',None,None,None)
        elapsed=now_ms-base.reference_ms
        bound=base.uncertainty_ms+math.ceil(elapsed*self.policy.max_drift_ppm/1_000_000)
        if elapsed>self.policy.max_age_ms:return Decision('CALIBRATION_EXPIRED','age budget exceeded',bound,elapsed,None)
        if bound>self.policy.max_uncertainty_ms:return Decision('UNCERTAINTY_EXPIRED','uncertainty budget exceeded',bound,elapsed,None)
        return Decision('WITHIN_DECLARED_ENVELOPE','prediction only; not a measurement',bound,elapsed,None)
    def audit(self,external_head=None):
        prev='0'*64
        for i,item in enumerate(self.log):
            if item.get('index')!=i or item.get('prev')!=prev or item.get('hash')!=hexdigest({k:v for k,v in item.items() if k!='hash'}):return 'TAMPERED'
            prev=item['hash']
        return 'EXTERNAL_HEAD_MISMATCH' if external_head is not None and external_head!=prev else 'VALID_LOCAL_CHAIN'

def fixture(seq,t,offset,u=2,root='fixture-root'):
    return Observation(seq,t,offset,u,root,hashlib.sha256(f'{seq}:{t}:{offset}:{root}'.encode()).hexdigest())

def demo():
    p=Policy(max_drift_ppm=100,max_age_ms=30_000,max_uncertainty_ms=12,jump_slack_ms=3)
    cases={}
    for kind,obs in [('nominal',fixture(1,10_000,1)),('jump',fixture(1,10_000,50)),('expired',fixture(1,40_000,0))]:
        ledger=DriftLedger(p,fixture(0,0,0))
        decision=ledger.check(obs)
        cases[kind]={'decision':asdict(decision),'ledger_audit':ledger.audit(),'active':ledger.active}
    ledger=DriftLedger(p,fixture(0,0,0))
    cases['forecast_10000']=asdict(ledger.forecast(10_000))
    return {'experiment':'JANE-168','scope':'local fixtures; no physical clock calibration','cases':cases,'learning_applied':False,'independent_custodians_verified':False}
if __name__=='__main__':print(json.dumps(demo(),indent=2))