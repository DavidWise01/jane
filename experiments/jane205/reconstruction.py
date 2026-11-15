"""JANE 205: exact binary aggregate reconstruction guard (synthetic, not DP)."""
import hashlib
import itertools
import json
import sqlite3
from dataclasses import dataclass
from fractions import Fraction


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def digest(x):
    return hashlib.sha256(canonical(x).encode('utf-8')).hexdigest()


class Reject(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Policy:
    dataset: str = 'holdout://frozen205'
    size: int = 4
    credits_cap: int = 12
    agents: tuple = ('ADA', 'BERT', 'CLIO')

    def __post_init__(self):
        if not isinstance(self.dataset, str) or not self.dataset or type(self.size) is not int or not 2 <= self.size <= 12:
            raise Reject('BAD_POLICY')
        if type(self.credits_cap) is not int or self.credits_cap < 1 or not self.agents or len(set(self.agents)) != len(self.agents) or any(not isinstance(a, str) or not a for a in self.agents):
            raise Reject('BAD_POLICY')


def rank(rows, n):
    """Exact rational row rank, independent of binary feasibility."""
    matrix = [[Fraction(int(i in row)) for i in range(n)] for row in rows]
    pivot = 0
    for col in range(n):
        found = next((r for r in range(pivot, len(matrix)) if matrix[r][col]), None)
        if found is None:
            continue
        matrix[pivot], matrix[found] = matrix[found], matrix[pivot]
        factor = matrix[pivot][col]
        matrix[pivot] = [v / factor for v in matrix[pivot]]
        for r in range(len(matrix)):
            if r != pivot and matrix[r][col]:
                k = matrix[r][col]
                matrix[r] = [v - k * w for v, w in zip(matrix[r], matrix[pivot])]
        pivot += 1
        if pivot == len(matrix):
            break
    return pivot


def analyze(events, size):
    rows = [tuple(e['subset']) for e in events]
    possibilities = []
    for bits in itertools.product((0, 1), repeat=size):
        if all(sum(bits[i] for i in e['subset']) == e['total'] for e in events):
            possibilities.append(bits)
    fixed = {str(i): possibilities[0][i] for i in range(size) if possibilities and all(p[i] == possibilities[0][i] for p in possibilities)}
    return {'rank': rank(rows, size), 'candidate_count': len(possibilities), 'fixed_coordinates': fixed,
            'fully_reconstructed': len(possibilities) == 1, 'consistent': bool(possibilities)}


class Ledger:
    def __init__(self, path=':memory:'):
        self.db = sqlite3.connect(str(path), isolation_level=None)
        self.db.execute('CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, body TEXT NOT NULL, previous TEXT NOT NULL, head TEXT NOT NULL)')
    def read(self):
        old = 'GENESIS'
        items = []
        for event_id, body, prev, head in self.db.execute('SELECT event_id,body,previous,head FROM events ORDER BY rowid'):
            try: event = json.loads(body)
            except (TypeError, ValueError) as exc: raise Reject('CORRUPT_LOG') from exc
            if not isinstance(event, dict) or event.get('event_id') != event_id or prev != old or digest({'previous': old, 'event': event}) != head:
                raise Reject('CORRUPT_LOG')
            items.append(event)
            old = head
        return items, old
    def append(self, event, validate):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            old_events, old_head = self.read()
            if any(e['event_id'] == event['event_id'] for e in old_events): raise Reject('REPLAY')
            verdict = validate(old_events, event)
            head = digest({'previous': old_head, 'event': event})
            self.db.execute('INSERT INTO events VALUES (?,?,?,?)', (event['event_id'], canonical(event), old_head, head))
            self.db.execute('COMMIT')
            return verdict
        except BaseException:
            self.db.execute('ROLLBACK')
            raise
    def close(self): self.db.close()


class FLAY205:
    def __init__(self, policy=None, path=':memory:'):
        self.policy = policy or Policy()
        self.ledger = Ledger(path)
    def _validate(self, previous, event):
        p = self.policy
        if type(event) is not dict or set(event) != {'event_id', 'agent', 'dataset', 'subset', 'total', 'credits', 'recipient', 'ancestry'}:
            raise Reject('BAD_EVENT')
        if any(not isinstance(event[x], str) or not event[x] for x in ('event_id','agent','dataset','recipient')):
            raise Reject('BAD_EVENT')
        if event['dataset'] != p.dataset: raise Reject('DATASET_MISMATCH')
        if event['agent'] not in p.agents: raise Reject('UNKNOWN_AGENT')
        subset = event['subset']
        if not isinstance(subset, list) or not subset or any(type(i) is not int or i < 0 or i >= p.size for i in subset) or subset != sorted(set(subset)):
            raise Reject('BAD_SUBSET')
        if type(event['total']) is not int or not 0 <= event['total'] <= len(subset): raise Reject('BAD_TOTAL')
        if type(event['credits']) is not int or event['credits'] < 1: raise Reject('BAD_CREDITS')
        if not isinstance(event['ancestry'], list) or event['ancestry'] != sorted(set(event['ancestry'])) or p.dataset not in event['ancestry']:
            raise Reject('BAD_ANCESTRY')
        if sum(e['credits'] for e in previous) + event['credits'] > p.credits_cap:
            raise Reject('BUDGET_EXCEEDED')
        before, after = analyze(previous, p.size), analyze(previous + [event], p.size)
        if not after['consistent']: raise Reject('INCONSISTENT_AGGREGATE')
        if after['candidate_count'] == 1: raise Reject('FULL_RECONSTRUCTION')
        if set(after['fixed_coordinates']) - set(before['fixed_coordinates']): raise Reject('COORDINATE_RECONSTRUCTION')
        return {'verdict': 'RELEASE_ALLOWED_FIXTURE', 'before': before, 'after': after,
                'cumulative_credits': sum(e['credits'] for e in previous) + event['credits']}
    def preview(self, event):
        prev, _ = self.ledger.read()
        if any(e['event_id'] == event.get('event_id') for e in prev): raise Reject('REPLAY')
        return self._validate(prev, event)
    def release(self, event): return self.ledger.append(event, self._validate)
    def state(self):
        entries, head = self.ledger.read()
        return {'verdict':'RECONSTRUCTION_GUARD_FIXTURE', 'events':len(entries), 'head':head,
                'analysis':analyze(entries,self.policy.size), 'credits_used':sum(e['credits'] for e in entries)}
    def close(self): self.ledger.close()


def item(event_id, agent, subset, total, credits=1, recipient='collector'):
    return {'event_id':event_id,'agent':agent,'dataset':'holdout://frozen205',
            'subset':sorted(subset),'total':total,'credits':credits,
            'recipient':recipient,'ancestry':['holdout://frozen205']}


def demonstration():
    flay = FLAY205()
    try:
        releases = []
        for e in (item('q1','ADA',[0,1],1),item('q2','BERT',[1,2],1),item('q3','CLIO',[2,3],1)):
            releases.append(flay.release(e))
        attempt = item('q4','ADA',[0,1,2],2)
        # For the 2 remaining candidates, query q4 with total 2 selects one unique world.
        try: flay.release(attempt); blocked = 'UNEXPECTED_ACCEPT'
        except Reject as exc: blocked = exc.code
        record = {'chapter':'JANE 205', 'invariant':'Budget Compliance != Reconstruction Resistance',
                  'releases':releases,'blocked':blocked,'state':flay.state(),
                  'frozen_parent':True, 'claim_scope':'synthetic binary aggregate fixtures only'}
        return record
    finally: flay.close()


if __name__ == '__main__': print(json.dumps(demonstration(),indent=2))
