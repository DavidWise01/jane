"""JANE 155 — exact inductive invariant checker for affine integer transitions.

Scope: nonnegative integers, nondeterministic choice of finite affine rules f(s)=a*s+b.
For all s>=0, preservation holds exactly when a>=0 and b>=0.
"""
from dataclasses import dataclass
from hashlib import sha256
import json

CHRONOS = '{{ 2026.11.13 }}{{ 13.06.00 }}{{ 123.45.56 }}'

def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=True)

def digest(v):
    return sha256(canonical(v).encode()).hexdigest()

@dataclass(frozen=True)
class Rule:
    name: str
    a: int
    b: int
    def __post_init__(self):
        if not self.name or not isinstance(self.a, int) or type(self.a) is bool or not isinstance(self.b, int) or type(self.b) is bool:
            raise ValueError('invalid rule')
        if abs(self.a)>1000 or abs(self.b)>100000:
            raise ValueError('coefficient budget')
    def apply(self, s):
        return self.a*s+self.b
    def minimum_failure(self):
        """Least nonnegative state mapped below zero, or None if impossible."""
        if self.b < 0:
            return 0
        if self.a < 0:
            return self.b//(-self.a)+1
        return None
    def certificate(self):
        bad=self.minimum_failure()
        return {'rule':self.name,'a':self.a,'b':self.b,
                'valid_for_all_nonnegative':bad is None,
                'proof':'a>=0 and b>=0 imply a*s+b>=0 for all integer s>=0' if bad is None else None,
                'minimum_counterexample':None if bad is None else {'input':bad,'output':self.apply(bad)}}

class Invariant155:
    def __init__(self, initial: int, rules, witness_root='owned:canonical', max_rules=32):
        self.initial=initial
        self.rules=tuple(rules)
        if type(initial) is not int or abs(initial)>1000000 or not 1<=len(self.rules)<=max_rules:
            raise ValueError('invalid initial/rule budget')
        if len({r.name for r in self.rules})!=len(self.rules):
            raise ValueError('duplicate rule')
        if not witness_root:
            raise ValueError('source root')
        self.root=witness_root
        self.active='frozen_parent'
        self.events=[]
        self._append('DECLARE',{'initial':initial,'rules':[r.__dict__ for r in self.rules],
                                'predicate':'s>=0','chronos':CHRONOS,'ancestry':witness_root})
    def _append(self, kind, payload):
        e={'seq':len(self.events),'kind':kind,'payload':payload,
           'prev':self.events[-1]['head'] if self.events else '0'*64}
        e['head']=digest(e)
        self.events.append(e)
    def finite_check(self, maximum=16):
        if type(maximum) is not int or not 0<=maximum<=10000:
            raise ValueError('finite budget')
        failures=[]
        for s in range(maximum+1):
            for rule in self.rules:
                if rule.apply(s)<0:
                    failures.append({'state':s,'rule':rule.name,'output':rule.apply(s)})
        return {'range':[0,maximum],'states_tested':maximum+1,'transitions_tested':(maximum+1)*len(self.rules),
                'failures':failures,'meaning':'finite search only — not a global proof'}
    def evaluate(self,finite_maximum=16):
        finite=self.finite_check(finite_maximum)
        certificates=[r.certificate() for r in self.rules]
        bad=[c for c in certificates if c['minimum_counterexample'] is not None]
        if self.initial < 0:
            status='INITIAL_OUTSIDE_REGION'
        elif bad:
            status='INDUCTIVE_STEP_FAILED'
        else:
            status='INDUCTIVE_INVARIANT_CERTIFIED'
        counterexamples=sorted(
            ({'rule':c['rule'],**c['minimum_counterexample']} for c in bad),
            key=lambda x:(x['input'],x['rule']))
        result={'version':'JANE-155','chronos':CHRONOS,'region':'all nonnegative integers',
                'predicate':'s>=0','initial_state':self.initial,'initial_valid':self.initial>=0,
                'certificates':certificates,'first_transition_counterexample':counterexamples[0] if counterexamples else None,
                'finite_sample':finite,'status':status,'proof_scope':'integer affine transitions only',
                'source_root':self.root,'independent_witness_increment':0,
                'active':self.active,'learning_applied':False,'jane_decision':'UNDECIDED'}
        result['digest']=digest(result)
        self._append('CHECK',{'result_digest':result['digest'],'status':status})
        return result
    def audit(self,external_head=None):
        prev='0'*64
        for i,e in enumerate(self.events):
            if e['seq']!=i or e['prev']!=prev or e['head']!=digest({k:v for k,v in e.items() if k!='head'}):
                return 'TAMPERED'
            prev=e['head']
        return 'EXTERNAL_HEAD_MISMATCH' if external_head is not None and external_head!=prev else 'VALID_LOCAL_CHAIN'

def demo():
    safe=Invariant155(0,[Rule('increment',1,1),Rule('double',2,0)])
    unsafe=Invariant155(0,[Rule('decrement',1,-1),Rule('increment',1,1)])
    latent=Invariant155(0,[Rule('hidden_negative_slope',-1,20)])
    return {'safe':safe.evaluate(5),'unsafe':unsafe.evaluate(5),'latent':latent.evaluate(5),
            'audits':[safe.audit(),unsafe.audit(),latent.audit()]}
if __name__=='__main__':
    print(json.dumps(demo(),indent=2))