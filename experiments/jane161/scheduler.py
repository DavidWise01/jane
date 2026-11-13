"""JANE 161: finite observation of bounded scheduler fairness.

Evidence, not a proof of infinite temporal fairness. The append-only SQLite log
stores observed scheduler ticks. An unobserved tick blocks definitive claims.
"""
import hashlib
import json
import sqlite3
from dataclasses import dataclass


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def hash_of(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


@dataclass(frozen=True)
class Contract:
    max_wait: int = 3
    def __post_init__(self):
        if type(self.max_wait) is not int or not (1 <= self.max_wait <= 10000):
            raise ValueError('max_wait must be an integer in [1, 10000]')


class Observer:
    def __init__(self, path=':memory:', contract=Contract()):
        self.db=sqlite3.connect(path)
        self.contract=contract
        self.db.execute('''CREATE TABLE IF NOT EXISTS observations (
          seq INTEGER PRIMARY KEY, stamp INTEGER NOT NULL, payload TEXT NOT NULL,
          prev TEXT NOT NULL, head TEXT NOT NULL)''')
        self.db.commit()

    def close(self):
        self.db.close()

    def record(self, stamp, enabled, chosen=None, observed=True):
        if type(stamp) is not int or stamp < 0:
            raise ValueError('stamp must be a nonnegative integer')
        if type(observed) is not bool:
            raise ValueError('observed must be boolean')
        if not isinstance(enabled, (list, tuple, set)) or any(not isinstance(v,str) or not v or len(v)>64 for v in enabled):
            raise ValueError('enabled names invalid')
        if len(enabled)>128 or len(set(enabled)) != len(enabled):
            raise ValueError('enabled names duplicated or over budget')
        if chosen is not None and (not isinstance(chosen,str) or not chosen):
            raise ValueError('chosen name invalid')
        if observed and chosen is not None and chosen not in enabled:
            raise ValueError('selected agent must be enabled')
        if not observed and chosen is not None:
            raise ValueError('unknown tick cannot specify selection')
        row=self.db.execute('SELECT seq, stamp, head FROM observations ORDER BY seq DESC LIMIT 1').fetchone()
        if row and stamp <= row[1]:
            raise ValueError('chronos must increase strictly')
        seq=0 if row is None else row[0]+1
        prev='0'*64 if row is None else row[2]
        payload={'enabled': sorted(enabled), 'chosen': chosen, 'observed': observed}
        doc={'seq':seq,'stamp':stamp,'payload':payload,'prev':prev}
        head=hash_of(doc)
        self.db.execute('INSERT INTO observations VALUES (?,?,?,?,?)',(seq,stamp,canonical(payload),prev,head))
        self.db.commit()
        return head

    def _rows(self):
        return [dict(seq=r[0], stamp=r[1],payload=json.loads(r[2]),prev=r[3],head=r[4])
                for r in self.db.execute('SELECT * FROM observations ORDER BY seq')]

    def audit(self, trusted_head=None):
        rows=self._rows();prev='0'*64;last_stamp=-1
        for i,r in enumerate(rows):
            if r['seq'] != i or r['stamp']<=last_stamp or r['prev']!=prev or hash_of({k:r[k] for k in ('seq','stamp','payload','prev')}) != r['head']:
                return 'TAMPERED'
            prev=r['head'];last_stamp=r['stamp']
        if trusted_head is not None and trusted_head != prev:
            return 'EXTERNAL_HEAD_MISMATCH'
        return 'VALID_LOCAL_CHAIN'

    def evaluate(self, trusted_head=None):
        audit=self.audit(trusted_head)
        if audit!='VALID_LOCAL_CHAIN':
            return {'status':'AUDIT_FAILURE','audit':audit,'violations':[], 'active':'frozen_parent'}
        rows=self._rows()
        if not rows:
            return {'status':'NO_OBSERVATIONS','audit':audit,'violations':[], 'active':'frozen_parent'}
        # Strict consecutive integer tick requirement; gaps are uncertainty, not evidence of fair service.
        uncertain=any(not r['payload']['observed'] for r in rows) or any(b['stamp']-a['stamp']!=1 for a,b in zip(rows,rows[1:]))
        streak={};violations=[];coverage=[]
        previous_tick=None
        for r in rows:
            p=r['payload'];tick=r['stamp'];active=set(p['enabled']) if p['observed'] else set()
            if previous_tick is not None and tick != previous_tick+1:
                streak={}
            previous_tick=tick
            for agent in list(streak):
                if agent not in active: del streak[agent]
            if not p['observed']:
                streak={};continue
            for agent in active:
                if agent==p['chosen']:
                    streak[agent]=0
                else:
                    streak[agent]=streak.get(agent,0)+1
                    if streak[agent]==self.contract.max_wait:
                        violations.append({'agent':agent,'deadline_tick':tick,'consecutive_unserved':streak[agent], 'stamp':tick})
            coverage.append({'stamp':tick,'enabled':len(active),'chosen':p['chosen']})
        # An omitted interval must not support a definitive whole-window compliance verdict.
        status=('BOUNDED_FAIRNESS_BREACH' if violations else
                'INCONCLUSIVE_OBSERVATION_GAP' if uncertain else
                'OBSERVED_WITHIN_BUDGET')
        result={'version':'JANE-161','contract':{'max_wait':self.contract.max_wait,'meaning':'consecutive fully observed enabled ticks without service'},
                'status':status,'audit':audit,'ticks':len(rows), 'coverage_complete':not uncertain,
                'violations':violations,'coverage':coverage,'head':rows[-1]['head'],
                'scope':'finite observed interval only; no assertion of infinite fairness',
                'active':'frozen_parent','learning_applied':False,'independent_witness_increment':0}
        result['digest']=hash_of(result)
        return result


def demonstration():
    o=Observer(contract=Contract(3))
    for tick,chosen in enumerate(['A','A','A','B','A']):
        o.record(tick,['A','B'],chosen)
    result=o.evaluate();o.close();return result

if __name__=='__main__':
    print(json.dumps(demonstration(),indent=2))