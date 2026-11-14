"""JANE 202: trace indirect sealed-test information into development decisions.
Synthetic, append-only evidence; claims of independence are not certified.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class InvalidEvidence(ValueError):
    pass


@dataclass(frozen=True)
class Event:
    event_id: str
    kind: str
    actor: str
    parents: tuple[str, ...] = ()
    dataset: str = ''
    model: str = ''
    payload: str = ''
    epoch: int = 0

    def record(self):
        return dict(event_id=self.event_id, kind=self.kind, actor=self.actor,
                    parents=list(self.parents), dataset=self.dataset,
                    model=self.model, payload=self.payload, epoch=self.epoch)


class FLAY202:
    TYPES = frozenset({'seal', 'access', 'score', 'summary', 'embedding', 'report',
                       'transfer', 'selection', 'evaluation', 'finalize', 'declassify'})
    INFO = frozenset({'score', 'summary', 'embedding', 'report', 'transfer', 'access', 'evaluation'})
    DECISIONS = frozenset({'selection', 'finalize'})

    def __init__(self, dataset='sealed-final', initial_model='model-0'):
        self.dataset = dataset
        self.initial_model = initial_model
        self.events = []
        self.head = '0' * 64
        self._ids = set()

    def append(self, event: Event):
        if not isinstance(event, Event) or event.kind not in self.TYPES:
            raise InvalidEvidence('unknown event')
        if not event.event_id or event.event_id in self._ids:
            raise InvalidEvidence('duplicate or empty event id')
        if not event.actor or type(event.epoch) is not int or event.epoch < 0:
            raise InvalidEvidence('invalid actor or epoch')
        if len(set(event.parents)) != len(event.parents):
            raise InvalidEvidence('repeated parent')
        if any(p not in self._ids for p in event.parents):
            raise InvalidEvidence('missing or future ancestor')
        if self.events and event.epoch < self.events[-1]['event']['epoch']:
            raise InvalidEvidence('nonmonotonic epoch')
        if event.kind == 'seal' and event.dataset != self.dataset:
            raise InvalidEvidence('wrong dataset sealed')
        if event.kind == 'declassify' and not event.parents:
            raise InvalidEvidence('unbound declassification')
        record = event.record()
        link = digest({'prior': self.head, 'event': record})
        self.events.append({'prior': self.head, 'event': record, 'hash': link})
        self.head = link
        self._ids.add(event.event_id)
        return link

    def intact(self):
        prior = '0' * 64
        ids = set()
        last_epoch = -1
        for row in self.events:
            ev = row['event']
            if row['prior'] != prior or row['hash'] != digest({'prior': prior, 'event': ev}):
                return False
            if ev['event_id'] in ids or any(p not in ids for p in ev['parents']):
                return False
            if ev['epoch'] < last_epoch:
                return False
            ids.add(ev['event_id'])
            last_epoch = ev['epoch']
            prior = row['hash']
        return prior == self.head and ids == self._ids

    def audit(self):
        if not self.intact():
            return {'verdict': 'CORRUPT_LOG', 'head': self.head}
        by_id = {r['event']['event_id']: r['event'] for r in self.events}
        if not any(e['kind'] == 'seal' for e in by_id.values()):
            return {'verdict': 'NO_SEALED_TEST', 'head': self.head}
        memo = {}

        def roots(event_id):
            if event_id in memo:
                return memo[event_id]
            ev = by_id[event_id]
            found = set()
            if ev['kind'] == 'seal' and ev['dataset'] == self.dataset:
                found.add(ev['event_id'])
            if ev['dataset'] == self.dataset and ev['kind'] in self.INFO:
                found.add('sealed-dataset-info')
            for parent in ev['parents']:
                found.update(roots(parent))
            memo[event_id] = frozenset(found)
            return memo[event_id]

        exposures = []
        affected = []
        declassified = set()
        for ev in by_id.values():
            r = roots(ev['event_id'])
            if ev['kind'] == 'declassify':
                declassified.update(ev['parents'])
            if ev['kind'] in self.INFO and r:
                exposures.append({'event': ev['event_id'], 'kind': ev['kind'],
                                  'actor': ev['actor'], 'sealed_ancestry': sorted(r)})
            if ev['kind'] in self.DECISIONS and r:
                affected.append({'event': ev['event_id'], 'model': ev['model'],
                                 'sealed_ancestry': sorted(r)})
        # Declassification never erases lineage or legitimizes previous adaptation.
        if affected:
            verdict = 'SEALED_INFORMATION_INFLUENCED_SELECTION'
        elif exposures:
            verdict = 'INDIRECT_EXPOSURE_NO_SELECTION_PATH'
        else:
            verdict = 'NO_RECORDED_EXPOSURE'
        return {'verdict': verdict, 'head': self.head, 'events': len(by_id),
                'exposures': exposures, 'affected_decisions': affected,
                'declared_declassifications': sorted(declassified),
                'scope': 'recorded lineage only; out-of-band disclosure not excluded'}


def fixture(scenario='summary_leak'):
    engine = FLAY202()
    add = engine.append
    add(Event('sealed', 'seal', 'custodian', dataset='sealed-final', epoch=1))
    add(Event('test', 'evaluation', 'evaluator', ('sealed',), 'sealed-final', 'model-0', epoch=2))
    if scenario == 'summary_leak':
        add(Event('agg', 'summary', 'evaluator', ('test',), payload='aggregate only', epoch=3))
        add(Event('partner', 'report', 'partner', ('agg',), payload='benchmark narrative', epoch=4))
        add(Event('select', 'selection', 'developer', ('partner',), model='model-1', epoch=5))
    elif scenario == 'embedding_leak':
        add(Event('vector', 'embedding', 'evaluator', ('test',), epoch=3))
        add(Event('select', 'selection', 'developer', ('vector',), model='model-1', epoch=4))
    elif scenario == 'score_leak':
        add(Event('score1', 'score', 'evaluator', ('test',), epoch=3))
        add(Event('select', 'selection', 'developer', ('score1',), model='model-1', epoch=4))
    elif scenario == 'isolated':
        add(Event('agg', 'summary', 'evaluator', ('test',), epoch=3))
        add(Event('select', 'selection', 'developer', model='model-1', epoch=4))
    elif scenario == 'no_access':
        pass
    elif scenario == 'declared_release':
        add(Event('agg', 'summary', 'evaluator', ('test',), epoch=3))
        add(Event('release', 'declassify', 'custodian', ('agg',), epoch=4))
        add(Event('select', 'selection', 'developer', ('agg',), model='model-1', epoch=5))
    else:
        raise ValueError('unknown scenario')
    return engine


if __name__ == '__main__':
    cases = {name: fixture(name).audit() for name in (
        'summary_leak', 'embedding_leak', 'score_leak', 'isolated', 'no_access', 'declared_release')}
    print(json.dumps({'experiment': 'JANE 202', 'cases': cases}, indent=2))