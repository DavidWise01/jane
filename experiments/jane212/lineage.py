"""JANE 212: declared search versus signed execution and reporting evidence.
All actors and custody roots in fixtures are synthetic, not proof of complete capture.
"""
from __future__ import annotations
import hashlib, json, sqlite3
from dataclasses import dataclass
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()

def seal(key, payload):
    return {'payload': payload, 'signature': key.sign(canonical(payload)).hex()}

def authenticate(obj, public_key):
    if not isinstance(obj, dict) or set(obj) != {'payload', 'signature'}:
        return False
    try:
        public_key.verify(bytes.fromhex(obj['signature']), canonical(obj['payload']))
        return True
    except (ValueError, TypeError, KeyError, InvalidSignature):
        return False


def chain(executions):
    head = '0' * 64
    heads = []
    for e in executions:
        head = digest({'previous': head, 'entry': e})
        heads.append(head)
    return heads

class Audit:
    def __init__(self, db=':memory:'):
        self.conn = sqlite3.connect(str(db))
        self.conn.execute('CREATE TABLE IF NOT EXISTS verdicts (nonce TEXT PRIMARY KEY, verdict TEXT, head TEXT)')
        self.conn.commit()

    def record(self, nonce, verdict):
        if not isinstance(nonce, str) or not nonce:
            raise ValueError('invalid nonce')
        last = self.conn.execute('SELECT head FROM verdicts ORDER BY rowid DESC LIMIT 1').fetchone()
        prev = last[0] if last else '0'*64
        head = digest({'prev':prev, 'nonce':nonce, 'verdict':verdict})
        try:
            self.conn.execute('INSERT INTO verdicts VALUES (?,?,?)',(nonce,verdict,head))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def verify(self):
        prev='0'*64
        for nonce, verdict, head in self.conn.execute('SELECT nonce,verdict,head FROM verdicts ORDER BY rowid'):
            if digest({'prev':prev,'nonce':nonce,'verdict':verdict}) != head:
                return False
            prev=head
        return True

    def close(self):
        self.conn.close()

class FLAY212:
    def __init__(self, plan_key: Ed25519PublicKey, execution_key: Ed25519PublicKey,
                 witness_keys: dict[str, Ed25519PublicKey], audit: Audit):
        self.plan_key=plan_key
        self.execution_key=execution_key
        self.witness_keys=witness_keys
        self.audit=audit

    def check(self, signed_plan, signed_execution, signed_witnesses, report):
        if not self.audit.verify():
            return {'verdict':'CORRUPT_AUDIT'}
        if not authenticate(signed_plan, self.plan_key):
            return {'verdict':'INVALID_PLAN_SIGNATURE'}
        if not authenticate(signed_execution, self.execution_key):
            return {'verdict':'INVALID_EXECUTION_SIGNATURE'}
        plan=signed_plan['payload']; run=signed_execution['payload']
        nonce=plan.get('nonce')
        if not isinstance(nonce,str) or len(nonce)<8:
            return {'verdict':'INVALID_NONCE'}
        qs=plan.get('queries')
        if not isinstance(qs,list) or not qs or any(not isinstance(x,str) or not x for x in qs) or len(set(qs))!=len(qs):
            return {'verdict':'INVALID_PLAN'}
        if plan.get('query_commitment')!=digest(qs):
            return {'verdict':'PLAN_COMMITMENT_MISMATCH'}
        executions=run.get('executions')
        if not isinstance(executions,list) or not all(isinstance(e,dict) and set(e)=={'id','query','result_hash'} for e in executions):
            return {'verdict':'INVALID_EXECUTIONS'}
        if any(not isinstance(e['id'],int) or isinstance(e['id'],bool) or e['id']<=0 or not isinstance(e['query'],str) or not isinstance(e['result_hash'],str) or len(e['result_hash'])!=64 for e in executions):
            return {'verdict':'INVALID_EXECUTIONS'}
        if run.get('nonce')!=nonce or run.get('plan_hash')!=digest(plan):
            return {'verdict':'EXECUTION_PLAN_MISMATCH'}
        actual_chain=chain(executions)
        if run.get('count')!=len(executions) or run.get('head')!=(actual_chain[-1] if actual_chain else '0'*64):
            return {'verdict':'EXECUTION_HEAD_MISMATCH'}
        if not isinstance(signed_witnesses,list) or len(signed_witnesses)<2:
            return {'verdict':'INSUFFICIENT_WITNESSES'}
        roots=set()
        for w in signed_witnesses:
            if not isinstance(w,dict) or set(w)!={'root','attestation'}:
                return {'verdict':'INVALID_WITNESS'}
            root=w['root']
            if root not in self.witness_keys or not authenticate(w['attestation'],self.witness_keys[root]):
                return {'verdict':'INVALID_WITNESS'}
            body=w['attestation']['payload']
            if body!={'nonce':nonce, 'plan_hash':digest(plan), 'execution_count':len(executions), 'execution_head':run['head']}:
                return {'verdict':'WITNESS_HEAD_CONFLICT'}
            roots.add(root)
        if len(roots)<2:
            return {'verdict':'SHARED_WITNESS_ANCESTRY'}
        if not isinstance(report,list) or any(not isinstance(r,dict) or set(r)!={'id','query','result_hash'} for r in report):
            return {'verdict':'INVALID_REPORT'}
        if len({r.get('id') for r in report if isinstance(r.get('id'),int)}) != len(report):
            return {'verdict':'DUPLICATE_REPORT_ID'}
        if not self.audit.record(nonce,'AUDITED'):
            return {'verdict':'REPLAY'}
        executed_ids=[e['id'] for e in executions]
        planned_ids=list(range(1,len(qs)+1))
        unplanned=[e['id'] for e in executions if e['id'] not in planned_ids or e['query'] != (qs[e['id']-1] if e['id'] in planned_ids else None)]
        missing_execution=[i for i in planned_ids if i not in executed_ids]
        extra_execution=bool(unplanned) or len(set(executed_ids))!=len(executed_ids)
        lookup={e['id']:e for e in executions}
        omitted=[i for i in executed_ids if i not in [r['id'] for r in report]]
        altered=[r['id'] for r in report if r.get('id') not in lookup or lookup[r['id']]!=r]
        if extra_execution:
            verdict='EXECUTION_OUTSIDE_COMMITTED_PLAN'
        elif missing_execution:
            verdict='PLANNED_EXECUTION_MISSING'
        elif omitted:
            verdict='EXECUTED_QUERY_OMITTED_FROM_REPORT'
        elif altered:
            verdict='REPORTED_RESULT_INCONSISTENT'
        else:
            verdict='DECLARED_SEARCH_CONSISTENT_FIXTURE'
        return {'verdict':verdict,'planned':len(qs),'executed':len(executions),'reported':len(report),
                'unplanned':unplanned,'missing_execution':missing_execution,'omitted':omitted,
                'altered':altered,'witness_roots':sorted(roots),
                'limitation':'Signed local witnesses cannot establish that all real executions were captured.'}


def fixture(kind='complete',nonce='jane212-demo-0001'):
    keys={name:Ed25519PrivateKey.generate() for name in ('plan','executor','alpha','beta')}
    queries=['subgroup:G01','subgroup:G02','subgroup:G03']
    plan={'nonce':nonce,'queries':queries,'query_commitment':digest(queries),'frozen':True}
    entries=[{'id':i+1,'query':q,'result_hash':digest({'query':q,'score':i+2})} for i,q in enumerate(queries)]
    report=list(entries)
    if kind=='omitted': report=report[:2]
    if kind=='unplanned': entries.append({'id':4,'query':'subgroup:G99','result_hash':digest('hidden')})
    if kind=='missing': entries=entries[:2];report=report[:2]
    if kind=='altered': report[-1]=dict(report[-1],result_hash=digest('changed'))
    run={'nonce':nonce,'plan_hash':digest(plan),'executions':entries,'count':len(entries),'head':chain(entries)[-1]}
    witnesses=[{'root':root,'attestation':seal(keys[root],{'nonce':nonce,'plan_hash':digest(plan),
              'execution_count':len(entries),'execution_head':run['head']})} for root in ('alpha','beta')]
    verifier=FLAY212(keys['plan'].public_key(),keys['executor'].public_key(),
                     {k:keys[k].public_key() for k in ('alpha','beta')},Audit())
    return verifier,seal(keys['plan'],plan),seal(keys['executor'],run),witnesses,report

if __name__=='__main__':
    output={}
    for kind in ('complete','omitted','unplanned','missing','altered'):
        v,p,r,w,report=fixture(kind)
        output[kind]=v.check(p,r,w,report)
        v.audit.close()
    print(json.dumps({'experiment':212,'results':output},indent=2,sort_keys=True))