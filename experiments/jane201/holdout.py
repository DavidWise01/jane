"""JANE 201: append-only, replayable holdout-use and exposure audit.

Fixture-only: logs are locally tamper-evident, not independently witnessed.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


class InvalidEvent(ValueError):
    pass


@dataclass(frozen=True)
class Event:
    seq: int
    kind: str
    set_id: str
    model: str
    payload: dict
    prev: str
    head: str

    def body(self):
        return {'seq': self.seq, 'kind': self.kind, 'set_id': self.set_id,
                'model': self.model, 'payload': self.payload, 'prev': self.prev}


class Ledger:
    """A local append-only event chain; signatures/remote custody not implied."""
    KINDS = {'FREEZE_SET', 'EVALUATE', 'DISCLOSE_SCORE', 'SELECT_MODEL',
             'SEAL_FINAL', 'FINAL_EVALUATE', 'FINAL_DISCLOSE', 'NOTE'}

    def __init__(self, events=()):
        self.events = []
        for e in events:
            self.append(e.kind, e.set_id, e.model, e.payload)
            if self.events[-1] != e:
                raise InvalidEvent('event chain does not match')

    @property
    def head(self):
        return self.events[-1].head if self.events else '0' * 64

    def append(self, kind, set_id, model='', payload=None):
        if kind not in self.KINDS:
            raise InvalidEvent('unknown event kind')
        if not isinstance(set_id, str) or not set_id or len(set_id) > 128:
            raise InvalidEvent('invalid set id')
        if not isinstance(model, str) or len(model) > 128:
            raise InvalidEvent('invalid model id')
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise InvalidEvent('invalid payload')
        # Deep copy through canonical JSON so caller mutation cannot change history.
        try:
            payload = json.loads(canonical(payload))
        except (TypeError, ValueError, OverflowError) as exc:
            raise InvalidEvent('noncanonical payload') from exc
        seq = len(self.events) + 1
        prev = self.head
        body = {'seq': seq, 'kind': kind, 'set_id': set_id, 'model': model,
                'payload': payload, 'prev': prev}
        event = Event(seq, kind, set_id, model, payload, prev, digest(body))
        self.events.append(event)
        return event

    def verify(self):
        prev = '0' * 64
        for seq, e in enumerate(self.events, 1):
            if e.seq != seq or e.prev != prev or digest(e.body()) != e.head:
                return False
            prev = e.head
        return True

    def export(self):
        return {'events': [e.body() | {'head': e.head} for e in self.events],
                'head': self.head}


class FLAY201:
    def __init__(self, ledger):
        self.ledger = ledger

    def audit(self, development_set, final_set):
        if not self.ledger.verify():
            return {'verdict': 'CORRUPT_LOG', 'reason': 'chain invalid'}
        if development_set == final_set:
            return {'verdict': 'SET_ALIAS', 'reason': 'final equals development'}
        histories = {development_set: [], final_set: []}
        for e in self.ledger.events:
            if e.set_id in histories:
                histories[e.set_id].append(e)
        dev = histories[development_set]
        fin = histories[final_set]
        def positions(items, kind):
            return [e.seq for e in items if e.kind == kind]
        freezes = positions(fin, 'FREEZE_SET')
        seals = positions(fin, 'SEAL_FINAL')
        finals = positions(fin, 'FINAL_EVALUATE')
        disclosure = positions(fin, 'FINAL_DISCLOSE')
        final_preseal_exposure = [e.seq for e in fin if e.kind in
                                  {'EVALUATE', 'DISCLOSE_SCORE', 'SELECT_MODEL',
                                   'FINAL_EVALUATE', 'FINAL_DISCLOSE'} and
                                  (not seals or e.seq < seals[0])]
        repeated_dev = len(positions(dev, 'EVALUATE')) > 1
        selection_dev = bool(positions(dev, 'SELECT_MODEL'))
        adaptation_dev = selection_dev and bool(positions(dev, 'DISCLOSE_SCORE'))
        reason = []
        if final_preseal_exposure:
            reason.append('final set exposed before seal')
        if len(freezes) != 1 or len(seals) != 1 or freezes[0] >= seals[0]:
            reason.append('missing or invalid frozen seal')
        if len(finals) > 1:
            reason.append('repeated final evaluation')
        if finals and seals and finals[0] < seals[0]:
            reason.append('final evaluation before seal')
        if disclosure and (not finals or min(disclosure) < max(finals)):
            reason.append('premature final disclosure')
        if len(disclosure) > 1:
            reason.append('repeated final disclosure')
        if finals:
            last_evaluation = max(finals)
            if any(e.seq > last_evaluation and e.kind in {'SELECT_MODEL', 'EVALUATE',
                       'DISCLOSE_SCORE'} for e in dev + fin):
                reason.append('model development after final exposure')
        # Observe direct overlap through explicit item-hash commitments, not names.
        def member_hashes(items):
            hashes = set()
            for e in items:
                if e.kind == 'FREEZE_SET':
                    xs = e.payload.get('members')
                    if isinstance(xs, list):
                        hashes.update(x for x in xs if isinstance(x, str))
            return hashes
        intersection = sorted(member_hashes(dev) & member_hashes(fin))
        if intersection:
            reason.append('frozen member overlap')
        if not finals:
            reason.append('final test not executed')
        verdict = 'FINAL_TEST_WITHHELD' if reason else 'SEALED_FINAL_FIXTURE'
        return {
            'verdict': verdict,
            'issues': reason,
            'final_exposure_preseal': final_preseal_exposure,
            'overlap_member_hashes': intersection,
            'development_evaluations': len(positions(dev, 'EVALUATE')),
            'development_reused': repeated_dev,
            'development_selection_after_feedback': adaptation_dev,
            'final_evaluations': len(finals),
            'final_disclosures': len(disclosure),
            'audit_head': self.ledger.head,
            'event_count': len(self.ledger.events),
            'limits': 'Local declared chronology and membership; no external custody or unseen access proof.'
        }


def fixture(mode='sealed'):
    chain = Ledger()
    chain.append('FREEZE_SET', 'development', payload={'members': ['d1', 'd2', 'd3']})
    chain.append('FREEZE_SET', 'final', payload={'members': ['f1', 'f2', 'f3']})
    if mode == 'leaked':
        chain.append('EVALUATE', 'final', 'm0', {'score': 0.8})
        chain.append('DISCLOSE_SCORE', 'final', 'm0', {'score': 0.8})
    chain.append('EVALUATE', 'development', 'm0', {'score': 0.6})
    chain.append('DISCLOSE_SCORE', 'development', 'm0', {'score': 0.6})
    chain.append('SELECT_MODEL', 'development', 'm1', {'based_on': 'm0-score'})
    chain.append('EVALUATE', 'development', 'm1', {'score': 0.9})
    chain.append('DISCLOSE_SCORE', 'development', 'm1', {'score': 0.9})
    chain.append('SEAL_FINAL', 'final', payload={'rule': 'single evaluation'})
    chain.append('FINAL_EVALUATE', 'final', 'm1', {'score': 0.7})
    chain.append('FINAL_DISCLOSE', 'final', 'm1', {'score': 0.7})
    if mode == 'retest':
        chain.append('FINAL_EVALUATE', 'final', 'm2', {'score': 0.8})
    if mode == 'adapt':
        chain.append('SELECT_MODEL', 'development', 'm2', {'based_on': 'final-score'})
    return chain


def demonstration():
    return {'experiment': 'JANE 201', 'invariant': 'Holdout reuse != independent validation',
            'cases': {name: FLAY201(fixture(name)).audit('development', 'final')
                      for name in ('sealed', 'leaked', 'retest', 'adapt')}}


if __name__ == '__main__':
    print(json.dumps(demonstration(), indent=2, sort_keys=True))