"""JANE 253: destination-enforced fencing, not a distributed consensus protocol.

The destination owns the epoch and checks it in the SAME SQLite write
transaction that commits an effect. A client-side precheck has no authority.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

class FenceError(Exception):
    pass

class Destination:
    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS authority (
                    resource TEXT PRIMARY KEY, epoch INTEGER NOT NULL,
                    holder TEXT NOT NULL, grant_id TEXT NOT NULL UNIQUE);
                CREATE TABLE IF NOT EXISTS effects (
                    resource TEXT NOT NULL, operation_id TEXT NOT NULL,
                    epoch INTEGER NOT NULL, holder TEXT NOT NULL,
                    payload_hash TEXT NOT NULL, payload TEXT NOT NULL,
                    PRIMARY KEY(resource, operation_id));
                CREATE TABLE IF NOT EXISTS attempts (
                    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource TEXT NOT NULL, operation_id TEXT NOT NULL,
                    epoch INTEGER NOT NULL, holder TEXT NOT NULL,
                    verdict TEXT NOT NULL);
            ''')

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        conn.execute('PRAGMA busy_timeout=5000')
        try:
            yield conn
        finally:
            if conn.in_transaction:
                conn.rollback()
            conn.close()

    @staticmethod
    def _valid(s: str) -> bool:
        return isinstance(s, str) and 0 < len(s) <= 160 and all(ch.isalnum() or ch in '-_.' for ch in s)

    def grant(self, resource: str, epoch: int, holder: str, grant_id: str) -> dict:
        if not all(map(self._valid, (resource, holder, grant_id))) or type(epoch) is not int or epoch < 1:
            raise FenceError('INVALID_GRANT')
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT epoch,holder,grant_id FROM authority WHERE resource=?',(resource,)).fetchone()
            if old is not None:
                if old == (epoch,holder,grant_id):
                    db.commit()
                    return {'verdict':'IDEMPOTENT_GRANT','epoch':epoch,'holder':holder}
                if epoch <= old[0]:
                    db.rollback()
                    raise FenceError('NON_MONOTONIC_GRANT')
            try:
                db.execute('INSERT INTO authority(resource,epoch,holder,grant_id) VALUES(?,?,?,?) '
                           'ON CONFLICT(resource) DO UPDATE SET epoch=excluded.epoch,holder=excluded.holder,grant_id=excluded.grant_id',
                           (resource,epoch,holder,grant_id))
            except sqlite3.IntegrityError as e:
                db.rollback()
                raise FenceError('DUPLICATE_GRANT_ID') from e
            db.commit()
            return {'verdict':'GRANTED','epoch':epoch,'holder':holder}

    def precheck(self, resource: str, epoch: int, holder: str) -> bool:
        """Advisory only: intentionally susceptible to TOCTOU races."""
        with self._connect() as db:
            row=db.execute('SELECT epoch,holder FROM authority WHERE resource=?',(resource,)).fetchone()
            return row == (epoch,holder)

    def commit(self, resource: str, epoch: int, holder: str, operation_id: str, payload: str) -> dict:
        if not all(map(self._valid,(resource,holder,operation_id))) or type(epoch) is not int or epoch < 1:
            raise FenceError('INVALID_OPERATION')
        if not isinstance(payload,str) or len(payload.encode('utf8'))>8192:
            raise FenceError('INVALID_PAYLOAD')
        digest=hashlib.sha256(payload.encode('utf8')).hexdigest()
        with self._connect() as db:
            # THE INVARIANT: grant epoch and effect write are serialized here.
            db.execute('BEGIN IMMEDIATE')
            current=db.execute('SELECT epoch,holder FROM authority WHERE resource=?',(resource,)).fetchone()
            if current != (epoch,holder):
                reason='FENCED_STALE_EPOCH' if current and epoch<current[0] else 'UNAUTHORIZED_DESTINATION_WRITE'
                db.execute('INSERT INTO attempts(resource,operation_id,epoch,holder,verdict) VALUES(?,?,?,?,?)',
                           (resource,operation_id,epoch,holder,reason))
                db.commit()
                return {'verdict':reason,'committed':False}
            existing=db.execute('SELECT epoch,holder,payload_hash FROM effects WHERE resource=? AND operation_id=?',
                                (resource,operation_id)).fetchone()
            if existing:
                verdict='IDEMPOTENT_REPLAY' if existing==(epoch,holder,digest) else 'OPERATION_ID_CONFLICT'
                db.execute('INSERT INTO attempts(resource,operation_id,epoch,holder,verdict) VALUES(?,?,?,?,?)',
                           (resource,operation_id,epoch,holder,verdict))
                db.commit()
                return {'verdict':verdict,'committed':False}
            db.execute('INSERT INTO effects(resource,operation_id,epoch,holder,payload_hash,payload) VALUES(?,?,?,?,?,?)',
                       (resource,operation_id,epoch,holder,digest,payload))
            db.execute('INSERT INTO attempts(resource,operation_id,epoch,holder,verdict) VALUES(?,?,?,?,?)',
                       (resource,operation_id,epoch,holder,'COMMITTED'))
            db.commit()
            return {'verdict':'COMMITTED','committed':True,'sha256':digest}

    def inspect(self, resource: str) -> dict:
        with self._connect() as db:
            a=db.execute('SELECT epoch,holder FROM authority WHERE resource=?',(resource,)).fetchone()
            effects=db.execute('SELECT operation_id,epoch,holder,payload_hash FROM effects WHERE resource=? ORDER BY rowid',(resource,)).fetchall()
            attempts=db.execute('SELECT operation_id,epoch,holder,verdict FROM attempts WHERE resource=? ORDER BY attempt_id',(resource,)).fetchall()
            return {'resource':resource,'authority':{'epoch':a[0],'holder':a[1]} if a else None,
                    'effects':[dict(zip(['operation_id','epoch','holder','payload_hash'],r)) for r in effects],
                    'attempts':[dict(zip(['operation_id','epoch','holder','verdict'],r)) for r in attempts],
                    'claim':'LOCAL_DESTINATION_TRANSACTION_ONLY','collective_choice':'UNRESOLVED','external_actions':0}

def demo(path: str) -> dict:
    p=Path(path)
    if p.exists(): p.unlink()
    d=Destination(p)
    d.grant('jane-task',1,'host-a','grant-a')
    a_prechecked=d.precheck('jane-task',1,'host-a')
    d.grant('jane-task',2,'host-b','grant-b')
    delayed_a=d.commit('jane-task',1,'host-a','a-delayed','old-host-effect')
    current_b=d.commit('jane-task',2,'host-b','b-work','new-host-effect')
    return {'experiment':'JANE-253','a_prechecked_before_takeover':a_prechecked,
            'a_delayed_attempt':delayed_a,'b_current_attempt':current_b,**d.inspect('jane-task')}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--db',default='demo-destination.sqlite');ap.add_argument('--output',default='result.json')
    args=ap.parse_args()
    result=demo(args.db)
    Path(args.output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print(json.dumps({'a':result['a_delayed_attempt']['verdict'],'b':result['b_current_attempt']['verdict'],'effects':len(result['effects'])}))