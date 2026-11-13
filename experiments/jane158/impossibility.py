"""JANE 158 — bounded-interval impossibility evidence.

The theorem is deliberately narrow: a globally enabled, nonzero integer
translation is enough to disprove any finite inductive interval containing an
initial state. Other transitions cannot make that force disappear.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def hash_of(value):
    return sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class Transition:
    name: str
    kind: str
    amount: int
    globally_enabled: bool = True

    def __post_init__(self):
        if not self.name or self.kind not in {'shift', 'reflect', 'set'}:
            raise ValueError('invalid transition')
        if type(self.amount) is not int or abs(self.amount) > 1000000:
            raise ValueError('invalid transition amount')
        if type(self.globally_enabled) is not bool:
            raise ValueError('invalid global enablement flag')

    def apply(self, s):
        if type(s) is not int:
            raise ValueError('state must be an integer')
        if self.kind == 'shift': return s + self.amount
        if self.kind == 'reflect': return self.amount - s
        return self.amount


@dataclass(frozen=True)
class Interval:
    low: int
    high: int

    def __post_init__(self):
        if type(self.low) is not int or type(self.high) is not int or self.low > self.high:
            raise ValueError('invalid interval')

    def contains(self, s): return self.low <= s <= self.high


def verify_local_interval(initial, interval, transitions):
    """Exact preservation for unguarded affine maps on a finite integer interval.

    Guarded/non-global transitions cannot be certified with this model.
    For a globally enabled shift or reflection, image extrema are at endpoints;
    for set, the image is a singleton. Thus endpoint checks suffice.
    """
    if not interval.contains(initial):
        return {'status': 'INITIAL_OUTSIDE', 'failure': {'initial': initial}}
    if any(not t.globally_enabled for t in transitions):
        return {'status': 'UNMODELED_GUARD', 'failure': None}
    for t in transitions:
        for s in (interval.low, interval.high):
            output = t.apply(s)
            if not interval.contains(output):
                return {'status': 'NOT_INDUCTIVE', 'failure': {
                    'transition': t.name, 'state': s, 'output': output,
                    'interval': [interval.low, interval.high]}}
    return {'status': 'INDUCTIVE_INTERVAL', 'failure': None}


def positive_escape(initial, upper, step):
    if step <= 0 or upper < initial:
        raise ValueError('invalid positive escape request')
    n = (upper - initial) // step + 1
    return {'steps': n, 'end': initial + n * step, 'closed_form': 's(n)=s0+n*k'}


def negative_escape(initial, lower, step):
    if step >= 0 or lower > initial:
        raise ValueError('invalid negative escape request')
    n = (initial - lower) // (-step) + 1
    return {'steps': n, 'end': initial + n * step, 'closed_form': 's(n)=s0+n*k'}


def verify_certificate(certificate):
    """Recompute an unboundedness certificate without trusting the producer."""
    try:
        s0 = certificate['initial']
        k = certificate['step']
        name = certificate['transition']
        if type(s0) is not int or type(k) is not int or not isinstance(name, str) or not name or k == 0:
            return False
        if certificate['scope'] != 'globally enabled integer translation':
            return False
        if certificate['claim'] != 'NO_FINITE_INDUCTIVE_INTERVAL_CONTAINING_INITIAL':
            return False
        # For every hypothetical finite endpoint U >= s0, k>0 implies
        # s0+n*k>U for n=floor((U-s0)/k)+1. The mirrored case applies k<0.
        # Check three arbitrary endpoints as a guard against incorrect arithmetic.
        offsets = (0, 1, 1000)
        for d in offsets:
            if k > 0:
                upper = s0 + d
                out = positive_escape(s0, upper, k)
                if out['end'] <= upper or out['steps'] < 1:
                    return False
            else:
                lower = s0 - d
                out = negative_escape(s0, lower, k)
                if out['end'] >= lower or out['steps'] < 1:
                    return False
        proof = {x: certificate[x] for x in ('initial', 'step', 'transition', 'scope', 'claim')}
        return certificate['digest'] == hash_of(proof)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def impossibility_certificate(initial, transition):
    if type(initial) is not int:
        raise ValueError('noninteger initial')
    if transition.kind != 'shift' or transition.amount == 0 or not transition.globally_enabled:
        return None
    proof = {
        'initial': initial,
        'step': transition.amount,
        'transition': transition.name,
        'scope': 'globally enabled integer translation',
        'claim': 'NO_FINITE_INDUCTIVE_INTERVAL_CONTAINING_INITIAL',
    }
    proof['digest'] = hash_of(proof)
    assert verify_certificate(proof)
    return proof


class Ledger:
    def __init__(self): self.events = []
    def append(self, kind, data):
        event = {'sequence': len(self.events), 'kind': kind, 'data': data,
                 'previous': self.events[-1]['head'] if self.events else '0' * 64}
        event['head'] = hash_of(event)
        self.events.append(event)
        return event['head']
    def verify(self, external_head=None):
        previous = '0' * 64
        for i, event in enumerate(self.events):
            if event['sequence'] != i or event['previous'] != previous:
                return 'CHAIN_BROKEN'
            if hash_of({k: v for k, v in event.items() if k != 'head'}) != event['head']:
                return 'CHAIN_BROKEN'
            previous = event['head']
        if external_head is not None and external_head != previous:
            return 'EXTERNAL_HEAD_MISMATCH'
        return 'VALID_LOCAL_CHAIN'


class FLAY158:
    def __init__(self, initial, transitions, max_candidates=8):
        if type(initial) is not int:
            raise ValueError('initial must be integer')
        if not transitions or len(transitions) > 16 or len(set(t.name for t in transitions)) != len(transitions):
            raise ValueError('invalid transitions')
        if type(max_candidates) is not int or not 1 <= max_candidates <= 64:
            raise ValueError('invalid bounded budget')
        self.initial, self.transitions = initial, tuple(transitions)
        self.max_candidates = max_candidates
        self.ledger = Ledger()
        self.parent = 'FROZEN'
        self.ledger.append('DECLARE', {'initial': initial, 'forces': [t.__dict__ for t in transitions],
                                       'budget': max_candidates})

    def evaluate(self):
        failures = []
        # Symmetric growing candidate intervals. Never implicitly claim a proof
        # from finite failed guesses.
        for radius in range(self.max_candidates):
            interval = Interval(self.initial-radius, self.initial+radius)
            outcome = verify_local_interval(self.initial, interval, self.transitions)
            rec = {'interval': [interval.low, interval.high], 'outcome': outcome}
            failures.append(rec)
            self.ledger.append('CANDIDATE_TEST', rec)
        proofs = [impossibility_certificate(self.initial, t) for t in self.transitions]
        proofs = [p for p in proofs if p]
        # Not finding a finite invariant is NOT a general impossibility theorem.
        status = 'PROVEN_NO_BOUNDED_INTERVAL' if proofs else 'NO_IMPOSSIBILITY_PROOF'
        result = {
            'version': 'JANE-158', 'status': status, 'initial': self.initial,
            'declared_forces': [t.__dict__ for t in self.transitions],
            'candidate_checks': failures, 'certificates': proofs,
            'proof_scope': 'unconditional integer translation sufficient condition only',
            'sample_failures_are_not_proof': True,
            'parent': self.parent, 'jane_activation': False,
            'learning_applied': False, 'external_custody_verified': False,
        }
        result['digest'] = hash_of(result)
        self.ledger.append('CONCLUDE', {'result_digest': result['digest'], 'status': status})
        result['local_ledger_head'] = self.ledger.events[-1]['head']
        return result


def demo():
    engine = FLAY158(0, [Transition('increment', 'shift', 1),
                         Transition('reflection', 'reflect', 20)], max_candidates=6)
    return engine, engine.evaluate()


if __name__ == '__main__':
    engine, result = demo()
    print(json.dumps({'result': result, 'audit': engine.ledger.verify()}, indent=2))