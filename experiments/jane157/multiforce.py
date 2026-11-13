"""JANE 157 — exact bounded integer affine invariant checking.

A declared closed interval is inductive iff the initial state is in it and
EVERY permitted affine integer transition maps its endpoints into it.
The endpoint argument holds because affine maps are monotone (or constant).
This is not a neural-network or external-witness proof.
"""
from dataclasses import dataclass
from hashlib import sha256
import json


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def digest(value):
    return sha256(canonical(value).encode('ascii')).hexdigest()


@dataclass(frozen=True)
class Region:
    lo: int
    hi: int

    def __post_init__(self):
        if type(self.lo) is not int or type(self.hi) is not int:
            raise ValueError('region bounds must be integers')
        if self.lo > self.hi or self.hi - self.lo > 256:
            raise ValueError('region invalid or beyond search cap')
        if max(abs(self.lo), abs(self.hi)) > 100_000:
            raise ValueError('region magnitude beyond cap')

    def contains(self, state):
        return self.lo <= state <= self.hi


@dataclass(frozen=True)
class Force:
    name: str
    a: int
    b: int

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name or len(self.name) > 48:
            raise ValueError('force name')
        if type(self.a) is not int or type(self.b) is not int:
            raise ValueError('coefficients must be integers')
        if abs(self.a) > 1000 or abs(self.b) > 100_000:
            raise ValueError('coefficient budget exceeded')

    def apply(self, x):
        return self.a * x + self.b


class FLAY157:
    def __init__(self, region, initial, forces, parent_head='f'*64):
        if not isinstance(region, Region) or type(initial) is not int:
            raise ValueError('region or initial')
        if not isinstance(forces, (tuple, list)) or not forces or len(forces) > 16:
            raise ValueError('force count')
        if not all(isinstance(f, Force) for f in forces):
            raise ValueError('unknown transition')
        if len({f.name for f in forces}) != len(forces):
            raise ValueError('duplicate force name')
        if not isinstance(parent_head, str) or len(parent_head) != 64 or any(c not in '0123456789abcdef' for c in parent_head):
            raise ValueError('parent digest')
        self.region, self.initial, self.forces = region, initial, tuple(forces)
        self.parent_head = parent_head
        self.active_parent = 'frozen'
        self.events = []
        self._append('DECLARED', {'region': region.__dict__, 'initial': initial,
            'forces': [f.__dict__ for f in self.forces], 'parent_head': parent_head})

    def _append(self, kind, data):
        item = {'seq':len(self.events), 'kind':kind, 'data':data,
                'prev':self.events[-1]['head'] if self.events else '0'*64}
        item['head'] = digest(item)
        self.events.append(item)

    def evaluate(self):
        initial_ok = self.region.contains(self.initial)
        inspections=[]
        for force in self.forces:
            low_image,high_image=force.apply(self.region.lo),force.apply(self.region.hi)
            min_image,max_image= min(low_image,high_image),max(low_image,high_image)
            preserved = min_image >= self.region.lo and max_image <= self.region.hi
            failure=None
            if not preserved:
                candidates=(s for s in range(self.region.lo,self.region.hi+1)
                            if not self.region.contains(force.apply(s)))
                first=min(candidates,key=lambda s:(abs(s),s))
                failure={'state':first,'next_state':force.apply(first),'force':force.name,
                         'trace':[first,force.apply(first)],'region':[self.region.lo,self.region.hi]}
            inspections.append({'force':force.name,'a':force.a,'b':force.b,
                'endpoint_images':[low_image,high_image], 'preserves':preserved,
                'smallest_failure':failure, 'method':'exact affine endpoint proof'})
        all_ok=all(item['preserves'] for item in inspections)
        status=('INITIAL_OUTSIDE_REGION' if not initial_ok else
                'MULTIFORCE_INVARIANT_PROVEN' if all_ok else 'MULTIFORCE_COUNTEREXAMPLES')
        report={'version':'JANE-157','status':status,'region':[self.region.lo,self.region.hi],
                'initial':self.initial,'initial_inside':initial_ok,
                'forces':inspections,'all_transitions_preserve':all_ok,
                'inductive':initial_ok and all_ok,
                'model_scope':'integer affine transitions on declared closed interval',
                'parent_unchanged':self.active_parent=='frozen',
                'jane_decision':'UNDECIDED','learning_applied':False,
                'independent_witnesses_observed':0}
        report['digest']=digest(report)
        self._append('ANALYZED',{'status':status,'report_digest':report['digest']})
        for item in inspections:
            if item['smallest_failure'] is not None:
                self._append('COUNTEREXAMPLE', item['smallest_failure'])
        return report

    def audit(self, held_head=None):
        previous='0'*64
        for n,item in enumerate(self.events):
            candidate={k:v for k,v in item.items() if k!='head'}
            if item['seq']!=n or item['prev']!=previous or digest(candidate)!=item['head']:
                return 'LEDGER_TAMPERED'
            previous=item['head']
        if held_head is not None and held_head!=previous:
            return 'EXTERNAL_HEAD_MISMATCH'
        return 'VALID_LOCAL_CHAIN'


def demonstration():
    region=Region(0,20)
    engine=FLAY157(region,0,[Force('reflection',-1,20), Force('increment',1,1),Force('doubling',2,0)])
    report=engine.evaluate()
    restricted=FLAY157(region,0,[Force('reflection',-1,20)])
    restricted_report=restricted.evaluate()
    return engine,report,restricted,restricted_report


if __name__=='__main__':
    e,report,r,restricted=demonstration()
    print(json.dumps({'combined':report,'restricted':restricted,
                      'audit':e.audit(),'restricted_audit':r.audit()},indent=2))