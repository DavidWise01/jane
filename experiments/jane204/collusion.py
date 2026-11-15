"""JANE 204 — deterministic, fixture-level cross-agent disclosure auditor.

Policy credits are not differential privacy or quantified bits. The ledger records only
submitted events. This is a prototype of ancestry and information-flow controls.
"""
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def digest(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()


class Reject(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Policy:
    dataset: str
    global_cap: int
    agent_cap: int
    recipient_cap: int
    allowed_agents: tuple
    def __post_init__(self):
        if not self.dataset or any(type(x) is not int or x < 1 for x in (self.global_cap, self.agent_cap, self.recipient_cap)):
            raise Reject('BAD_POLICY')
        if not self.allowed_agents or len(set(self.allowed_agents)) != len(self.allowed_agents):
            raise Reject('BAD_AGENTS')


class Ledger:
    def __init__(self, path=':memory:'):
        self.db = sqlite3.connect(str(path), isolation_level=None)
        self.db.execute('PRAGMA busy_timeout=5000')
        self.db.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, body TEXT NOT NULL, previous TEXT NOT NULL, head TEXT NOT NULL)')
    def entries(self):
        return [dict(zip(('id', 'body', 'previous', 'head'), row)) for row in self.db.execute('SELECT id,body,previous,head FROM events ORDER BY rowid')]
    def check_chain(self):
        old = 'GENESIS'
        decoded = []
        for e in self.entries():
            try: b = json.loads(e['body'])
            except (TypeError, ValueError): raise Reject('CORRUPT_LOG')
            if e['previous'] != old or e['head'] != digest({'previous': old, 'body': b}) or b.get('event_id') != e['id']:
                raise Reject('CORRUPT_LOG')
            old = e['head']
            decoded.append(b)
        return decoded, old
    def append(self, event, validator):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            rows, prev = self.check_chain()
            if any(x['event_id'] == event['event_id'] for x in rows): raise Reject('REPLAY')
            validator(rows, event)
            head = digest({'previous': prev, 'body': event})
            self.db.execute('INSERT INTO events VALUES (?,?,?,?)', (event['event_id'], canonical(event), prev, head))
            self.db.execute('COMMIT')
            return head
        except BaseException:
            self.db.execute('ROLLBACK')
            raise
    def close(self): self.db.close()
    def __del__(self):
        try: self.db.close()
        except (AttributeError, sqlite3.ProgrammingError): pass


class FLAY204:
    def __init__(self, policy, path=':memory:'):
        self.policy = policy
        self.ledger = Ledger(path)

    def _validate(self, previous, e):
        p = self.policy
        required = {'event_id', 'agent', 'recipient', 'dataset', 'subset', 'credits', 'source_roots', 'payload_hash'}
        if set(e) != required or not all(isinstance(e[k], str) and e[k] for k in ('event_id','agent','recipient','dataset','payload_hash')):
            raise Reject('BAD_EVENT')
        if e['dataset'] != p.dataset: raise Reject('DATASET_MISMATCH')
        if e['agent'] not in p.allowed_agents: raise Reject('UNREGISTERED_AGENT')
        if type(e['credits']) is not int or e['credits'] <= 0: raise Reject('BAD_CREDITS')
        if not isinstance(e['subset'], list) or not e['subset'] or any(type(v) is not int or v < 0 for v in e['subset']) or len(set(e['subset'])) != len(e['subset']):
            raise Reject('BAD_SUBSET')
        if e['subset'] != sorted(e['subset']): raise Reject('NONCANONICAL_SUBSET')
        if not isinstance(e['source_roots'], list) or not e['source_roots'] or any(not isinstance(x,str) or not x for x in e['source_roots']) or len(set(e['source_roots'])) != len(e['source_roots']):
            raise Reject('BAD_ANCESTRY')
        if e['source_roots'] != sorted(e['source_roots']): raise Reject('NONCANONICAL_ANCESTRY')
        if p.dataset not in e['source_roots']: raise Reject('MISSING_DATASET_ANCESTRY')
        # Charging each released output, including reruns and repeated payloads, is conservative.
        if sum(x['credits'] for x in previous) + e['credits'] > p.global_cap: raise Reject('GLOBAL_BUDGET_EXCEEDED')
        if sum(x['credits'] for x in previous if x['agent'] == e['agent']) + e['credits'] > p.agent_cap: raise Reject('AGENT_BUDGET_EXCEEDED')
        if sum(x['credits'] for x in previous if x['recipient'] == e['recipient']) + e['credits'] > p.recipient_cap:
            raise Reject('RECIPIENT_BUDGET_EXCEEDED')

    def release(self, event_id, agent, recipient, subset, credits, payload, source_roots=None):
        e = {'event_id':event_id,'agent':agent,'recipient':recipient,'dataset':self.policy.dataset,
             'subset':list(subset),'credits':credits,'payload_hash':digest(payload),
             'source_roots':list(source_roots if source_roots is not None else [self.policy.dataset])}
        head = self.ledger.append(e, self._validate)
        return {'verdict':'RELEASE_RECORDED_FIXTURE', 'event_id':event_id, 'head':head, 'audit':self.audit()}

    def audit(self):
        rows, head = self.ledger.check_chain()
        per_agent = {a:sum(r['credits'] for r in rows if r['agent']==a) for a in self.policy.allowed_agents}
        recipients = sorted(set(r['recipient'] for r in rows))
        groups = {}
        for recipient in recipients:
            rs = [r for r in rows if r['recipient']==recipient]
            groups[recipient] = {'agents':sorted(set(r['agent'] for r in rs)),
                                 'credits':sum(r['credits'] for r in rs),
                                 'union_subset':sorted(set(v for r in rs for v in r['subset'])),
                                 'shared_roots':sorted(set.intersection(*(set(r['source_roots']) for r in rs))) if rs else []}
        total = sum(r['credits'] for r in rows)
        return {'verdict':'RECORDED_COMPLIANT_NOT_PROVEN_SECRET','global_credits':total,
                'global_cap':self.policy.global_cap, 'agents':per_agent,
                'recipient_groups':groups,'events':len(rows),'head':head,
                'distinct_payloads':len(set(r['payload_hash'] for r in rows)),
                'caveat':'No proof of unreported agent communication, physical independence, or privacy.'}


def fixture():
    p = Policy('holdout-204',12,8,8,('ada','bert','clio'))
    f = FLAY204(p)
    events = []
    events.append(f.release('e1','ada','collector',[0,1,2],4,{'score':0.7}))
    events.append(f.release('e2','bert','collector',[2,3,4],4,{'score':0.8}))
    try: f.release('e3','clio','collector',[4,5,6],1,{'score':0.9})
    except Reject as exc: refusal = exc.code
    events.append(f.release('e4','clio','other',[4,5,6],3,{'score':0.9}))
    try: f.release('e5','bert','other',[6,7,8],2,{'score':0.9})
    except Reject as exc: global_refusal=exc.code
    snapshot=f.audit()
    f.ledger.close()
    return {'chapter':'JANE 204','invariant':'Independent Query Budgets != Independent Information',
            'policy':{'global':p.global_cap,'agent':p.agent_cap,'recipient':p.recipient_cap},
            'recipient_refusal':refusal,'global_refusal':global_refusal,
            'audit':snapshot,'event_ids':['e1','e2','e4'],'verified_fixture_only':True}


if __name__=='__main__': print(json.dumps(fixture(),indent=2,sort_keys=True))