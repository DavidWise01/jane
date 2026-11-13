"""JANE 159 — deterministic guarded integer transition reachability.

Finite exhaustive exploration yields a complete result only when all reachable
states and enabled successors fit within the state budget. A proven unbounded
witness is restricted to a globally enabled positive translation; other
incomplete explorations return UNKNOWN rather than claiming impossibility.
"""
from dataclasses import dataclass, asdict
from collections import deque
import hashlib, json


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'))


def sha(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()


@dataclass(frozen=True)
class Rule:
    name: str
    delta: int
    guard: str = 'always'
    threshold: int = 0

    def __post_init__(self):
        if not self.name or not isinstance(self.delta, int) or type(self.delta) is not int:
            raise ValueError('bad rule')
        if self.guard not in ('always', 'lt', 'le', 'gt', 'ge', 'eq'):
            raise ValueError('unsupported guard')
        if type(self.threshold) is not int or abs(self.threshold) > 100000:
            raise ValueError('bad threshold')

    def enabled(self, s):
        return {'always': lambda: True, 'lt': lambda: s < self.threshold,
                'le': lambda: s <= self.threshold, 'gt': lambda: s > self.threshold,
                'ge': lambda: s >= self.threshold, 'eq': lambda: s == self.threshold}[self.guard]()

    def apply(self, s):
        if not self.enabled(s):
            raise ValueError('disabled transition')
        return s + self.delta


class FLAY159:
    def __init__(self, start, rules, lower=0, upper=20, max_states=128):
        if type(start) is not int or type(lower) is not int or type(upper) is not int or lower > upper:
            raise ValueError('bad states or proposed bounds')
        if not isinstance(rules, (tuple, list)) or not rules or any(not isinstance(r, Rule) for r in rules):
            raise ValueError('rules required')
        if len({r.name for r in rules}) != len(rules):
            raise ValueError('duplicate force identity')
        if type(max_states) is not int or not 1 <= max_states <= 10000:
            raise ValueError('budget must be 1..10000')
        self.start, self.rules = start, tuple(sorted(rules, key=lambda r:r.name))
        self.lower, self.upper, self.max_states = lower, upper, max_states
        self.entries = []
        self._record('DECLARE', {'start':start, 'rules':[asdict(r) for r in self.rules], 'claimed_bounds':[lower, upper], 'max_states':max_states})

    def _record(self, kind, payload):
        datum = {'index':len(self.entries), 'kind':kind, 'payload':payload,
                 'previous':self.entries[-1]['hash'] if self.entries else '0'*64}
        datum['hash'] = sha(datum)
        self.entries.append(datum)

    def audit(self, externally_held_head=None):
        previous = '0'*64
        for index, event in enumerate(self.entries):
            data = {k:v for k,v in event.items() if k != 'hash'}
            if event['index'] != index or event['previous'] != previous or event['hash'] != sha(data):
                return 'LOCAL_LEDGER_TAMPERED'
            previous = event['hash']
        if externally_held_head is not None and externally_held_head != previous:
            return 'EXTERNAL_HEAD_MISMATCH'
        return 'LOCAL_LEDGER_VALID'

    def run(self):
        # Breadth-first exploration; one recorded predecessor per state.
        parents = {self.start:None}
        queue = deque([self.start]); examined = 0; edges = []
        breach = ({"from":None,"rule":"INITIAL_STATE","to":self.start,"path":[]}
                  if not self.lower <= self.start <= self.upper else None); omitted = False
        while queue:
            s = queue.popleft(); examined += 1
            for rule in self.rules:
                if not rule.enabled(s):
                    continue
                nxt = rule.apply(s)
                edges.append((s,rule.name,nxt))
                if not self.lower <= nxt <= self.upper and breach is None:
                    # Path includes initial start and all verified enabled steps.
                    steps = [(s,rule.name,nxt)]
                    cursor = s
                    while parents[cursor] is not None:
                        prior, via = parents[cursor]
                        steps.append((prior,via,cursor)); cursor = prior
                    steps.reverse()
                    breach = {'from':s,'rule':rule.name,'to':nxt,'path':[list(v) for v in steps]}
                if nxt not in parents:
                    if len(parents) >= self.max_states:
                        omitted = True
                    else:
                        parents[nxt] = (s,rule.name)
                        queue.append(nxt)
            if omitted:
                break
        complete = not omitted and not queue
        # Any globally enabled positive translation can be repeated indefinitely.
        # For a full multi-rule system it remains an allowed path regardless of other rules.
        global_drift = next((r for r in self.rules if r.guard == 'always' and r.delta > 0),None)
        status = ('BOUND_VIOLATED' if breach is not None else
                  'BOUNDED_REACHABLE_SET' if complete else 'INCONCLUSIVE_BUDGET')
        certificate = None
        if global_drift:
            certificate = {'kind':'UNBOUNDED_ALLOWED_PATH', 'rule':global_drift.name,
                           'delta':global_drift.delta,
                           'reason':'repeated globally enabled positive translation',
                           'sequence':'s(n)=start+n*delta for every natural n'}
        result = {'experiment':'JANE-159', 'status':status, 'initial':self.start,
                  'claimed_bounds':[self.lower,self.upper],
                  'states_seen':len(parents),'states_examined':examined,
                  'enabled_edges_examined':len(edges), 'complete':complete,
                  'counterexample':breach,'unbounded_path_certificate':certificate,
                  'assumptions':'integer states, additive transitions, guards as declared, nondeterministic choice; bounded by explicit exploration budget',
                  'scope':'complete reachable graph only when complete=True; global positive drift certificate independently valid',
                  'active_parent':'FROZEN', 'learning_applied':False, 'witness_votes_added':0}
        result['digest']=sha(result)
        self._record('ANALYZE',{'result_digest':result['digest'],'status':status,'counterexample':breach,'certificate':certificate})
        return result


def demo():
    capped = FLAY159(0,[Rule('increment_below_20',1,'lt',20)],0,20)
    free = FLAY159(0,[Rule('unconditional_increment',1)],0,20,max_states=32)
    return {'guarded':capped.run(), 'unconditional':free.run(),
            'guarded_audit':capped.audit(),'unconditional_audit':free.audit()}

if __name__=='__main__':
    print(json.dumps(demo(),indent=2))
