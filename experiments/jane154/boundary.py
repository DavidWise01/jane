"""JANE 154 — finite domain boundary exploration with append-only evidence.

No inference outside inspected states; no live witnessing or activation.
"""
from dataclasses import dataclass
from hashlib import sha256
import json

CHRONOS = "{{ 2026.11.13 }}{{ 13.06.00 }}{{ 123.45.56 }}"


def digest(x):
    return sha256(json.dumps(x, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class Operation:
    kind: str
    argument: int

    def __post_init__(self):
        if self.kind not in ('set', 'add', 'multiply', 'nonnegative_add'):
            raise ValueError('operation')
        if type(self.argument) is not int or abs(self.argument) > 100:
            raise ValueError('argument')

    def apply(self, value):
        if type(value) is not int or abs(value) > 100000:
            raise ValueError('state')
        if self.kind == 'set':
            return self.argument
        if self.kind == 'add':
            return value + self.argument
        if self.kind == 'multiply':
            return value * self.argument
        if value < 0:
            raise ValueError('requires nonnegative input')
        return value + self.argument


def execute(state, first, second):
    trace = [state]
    try:
        intermediate = first.apply(state)
        trace.append(intermediate)
        result = second.apply(intermediate)
        trace.append(result)
        return {'valid': True, 'trace': trace, 'result': result}
    except ValueError as exc:
        return {'valid': False, 'trace': trace, 'result': None, 'error': str(exc)}


def compare(state, a, b):
    ab = execute(state, a, b)
    ba = execute(state, b, a)
    same = ab['valid'] and ba['valid'] and ab['result'] == ba['result']
    return {'state': state, 'AB': ab, 'BA': ba, 'compatible': same,
            'reason': 'MATCH' if same else 'INVALID_ORDER' if not ab['valid'] or not ba['valid'] else 'DIFFERENT_RESULT'}


@dataclass(frozen=True)
class Declaration:
    low: int
    high: int
    step_budget: int
    floor: int = -1000
    ceiling: int = 1000

    def __post_init__(self):
        if any(type(x) is not int for x in (self.low, self.high, self.step_budget, self.floor, self.ceiling)):
            raise ValueError('integers required')
        if not self.floor <= self.low <= self.high <= self.ceiling:
            raise ValueError('range')
        if self.high-self.low > 64 or not 0 <= self.step_budget <= 128:
            raise ValueError('budget')


class FLAY:
    def __init__(self, a, b, declaration, ancestor_hash='f'*64):
        if len(ancestor_hash) != 64 or any(c not in '0123456789abcdef' for c in ancestor_hash):
            raise ValueError('ancestor')
        self.a, self.b, self.declaration = a, b, declaration
        self.ancestor_hash = ancestor_hash
        self.events = []
        self.active = 'frozen_parent'
        self._append('DECLARE', {'a': a.__dict__, 'b': b.__dict__, 'domain': declaration.__dict__,
                                 'chronos': CHRONOS, 'ancestor': ancestor_hash})

    def _append(self, kind, payload):
        item = {'sequence': len(self.events), 'kind': kind, 'payload': payload,
                'previous': self.events[-1]['head'] if self.events else '0'*64}
        item['head'] = digest(item)
        self.events.append(item)

    def audit(self, external_head=None):
        previous = '0'*64
        for n, event in enumerate(self.events):
            if (event['sequence'] != n or event['previous'] != previous or
                    digest({k: v for k, v in event.items() if k != 'head'}) != event['head']):
                return 'TAMPERED'
            previous = event['head']
        if external_head is not None and external_head != previous:
            return 'EXTERNAL_HEAD_MISMATCH'
        return 'VALID_LOCAL_CHAIN'

    def explore(self):
        d = self.declaration
        core = []
        for state in range(d.low, d.high + 1):
            record = compare(state, self.a, self.b)
            core.append(record)
            self._append('CORE', record)
        core_pass = all(record['compatible'] for record in core)
        checked = set(range(d.low, d.high+1))
        found = {'left': None, 'right': None}
        passed = {'left': [], 'right': []}
        exhausted = {'left': d.low == d.floor, 'right': d.high == d.ceiling}
        trials = 0
        # Deterministic alternating frontier: left, right, left, right.
        for distance in range(1, d.step_budget + 1):
            side = 'left' if distance % 2 else 'right'
            if found[side] is not None or exhausted[side]:
                # The budget counts *tests*, not iterations, so continue with other side.
                other = 'right' if side == 'left' else 'left'
                if found[other] is not None or exhausted[other]:
                    break
                side = other
            state = (d.low - (len(passed['left']) + 1) if side == 'left' else
                     d.high + (len(passed['right']) + 1))
            if state < d.floor or state > d.ceiling:
                exhausted[side] = True
                continue
            if state in checked:
                raise AssertionError('duplicate exploration')
            checked.add(state)
            record = compare(state, self.a, self.b)
            self._append('EXPLORE_'+side.upper(), record)
            trials += 1
            if record['compatible']:
                passed[side].append(state)
            else:
                found[side] = record
            if found['left'] is not None and found['right'] is not None:
                break
        # A missing failure means untested or terminated at the declared outer boundary.
        status = ('CORE_INVALID' if not core_pass else
                  'BOUNDARY_COUNTEREXAMPLE' if any(found.values()) else
                  'BUDGET_OR_DOMAIN_LIMIT')
        result = {'version': 'JANE-154', 'chronos': CHRONOS, 'declared_core': [d.low, d.high],
                  'state_floor_ceiling': [d.floor, d.ceiling], 'budget': d.step_budget,
                  'core_verified': core_pass, 'core_count': len(core),
                  'states_tested_outside': trials, 'tested_outside': passed,
                  'first_failure': found, 'status': status,
                  'scope': 'finite explicitly tested integer states only',
                  'active': self.active, 'jane_decision': 'UNDECIDED',
                  'learning_applied': False, 'independent_witness_increment': 0}
        result['digest'] = digest(result)
        self._append('RESULT', {'result_digest': result['digest'], 'status': status})
        return result


def demo():
    # From JANE 153: set(0), then nonnegative_add(0).
    # On 0..3 they commute; -1 violates B's precondition when B executes first.
    engine = FLAY(Operation('set', 0), Operation('nonnegative_add', 0),
                  Declaration(low=0, high=3, step_budget=6, floor=-3, ceiling=6))
    return engine, engine.explore()


if __name__ == '__main__':
    f, result = demo()
    print(json.dumps({'result': result, 'audit': f.audit()}, indent=2))
