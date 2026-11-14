"""JANE 163: independently auditable *claims* to signed sequence ranges.

Trust anchor identities are configuration assertions, not evidence of real-world
operational independence. Local hashes do not prove physical execution.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

ZERO='0'*64

def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',',':'), ensure_ascii=True).encode()
def sha(value):return hashlib.sha256(canon(value)).hexdigest()
def key_hex(private):
    from cryptography.hazmat.primitives import serialization
    return private.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex()
def sign(private,record):return private.sign(canon(record)).hex()
def verify(public_hex, record, sig):
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex)).verify(bytes.fromhex(sig),canon(record))
        return True
    except (ValueError,InvalidSignature):return False

def scheduler_records(n=6):
    result=[];prev=ZERO
    for sequence in range(1,n+1):
        body={'sequence':sequence,'enabled':['A','B'],'selected':'A' if sequence%2 else 'B','previous':prev}
        head=sha(body); result.append({**body,'head':head});prev=head
    return result

def validate_scheduler(records):
    prev=ZERO
    for i,record in enumerate(records,1):
        if record.get('sequence')!=i or record.get('previous')!=prev or record.get('head')!=sha({k:v for k,v in record.items() if k!='head'}):
            return False
        prev=record['head']
    return True

def checkpoint(records,start,end,root,admin,nonce,stamp='2026-11-13T19:50:00-06:00'):
    if start<1 or end<start or end>len(records) or not validate_scheduler(records):raise ValueError('invalid signed range source')
    return {'protocol':'JANE-163','root':root,'admin':admin,'start':start,'end':end,
            'previous_head':records[start-2]['head'] if start>1 else ZERO,
            'end_head':records[end-1]['head'],'nonce':nonce,'chronos':stamp}

def envelope(private,body):return {'body':body,'signature':sign(private,body)}

@dataclass(frozen=True)
class Root:
    key: str
    admin: str

class Auditor:
    """Append-only SQLite observations and identity-aware checkpoint audit."""
    def __init__(self,path,roots,expected_end=None):
        self.path=str(path);self.roots=roots;self.expected_end=expected_end
        self.db=sqlite3.connect(self.path)
        self.db.execute('CREATE TABLE IF NOT EXISTS observations(id INTEGER PRIMARY KEY, payload TEXT NOT NULL, prev TEXT NOT NULL, head TEXT NOT NULL)')
        self.db.commit()
    def close(self):self.db.close()
    def observe(self,payload):
        previous=self.db.execute('SELECT head FROM observations ORDER BY id DESC LIMIT 1').fetchone()
        prev=previous[0] if previous else ZERO
        doc={'payload':payload,'prev':prev};head=sha(doc)
        self.db.execute('INSERT INTO observations(payload,prev,head) VALUES (?,?,?)',(json.dumps(payload,sort_keys=True),prev,head));self.db.commit()
        return head
    def chain_status(self,external_head=None):
        prev=ZERO
        for idx,payload,prior,head in self.db.execute('SELECT id,payload,prev,head FROM observations ORDER BY id'):
            try:decoded=json.loads(payload)
            except json.JSONDecodeError:return 'LOCAL_TAMPER'
            if prior!=prev or sha({'payload':decoded,'prev':prior})!=head:return 'LOCAL_TAMPER'
            prev=head
        if external_head is not None and external_head!=prev:return 'EXTERNAL_HEAD_MISMATCH'
        return 'VALID_LOCAL_CHAIN'
    def audit(self,envelopes,scheduler=None):
        accepted=[];rejected=[];used=set(); identity={}
        for item in envelopes:
            try:
                b=item['body'];root=b['root'];r=self.roots.get(root)
                if not r or not verify(r.key,b,item['signature']):raise ValueError('BAD_SIGNATURE_OR_UNKNOWN_ROOT')
                if b['protocol']!='JANE-163' or b['admin']!=r.admin or type(b['start']) is not int or type(b['end']) is not int or b['start']<1 or b['end']<b['start']:
                    raise ValueError('INVALID_CLAIM')
                if not isinstance(b['nonce'],str) or not b['nonce']:raise ValueError('INVALID_NONCE')
                ident=(root,b['nonce'])
                if ident in used:raise ValueError('REPLAY')
                used.add(ident)
                if root in identity and identity[root]!=r.admin:raise ValueError('ROOT_IDENTITY_CONFLICT')
                identity[root]=r.admin
                accepted.append(b)
            except (ValueError,KeyError,TypeError) as e:
                rejected.append(str(e))
        # Roots belonging to one declared administrator supply one custody vote.
        admin_groups={}
        for b in accepted:admin_groups.setdefault(b['admin'],set()).add(b['root'])
        independent_claims=len(admin_groups)
        conflicts=[]
        for i,a in enumerate(accepted):
            for b in accepted[i+1:]:
                if a['start']==b['start'] and a['end']==b['end'] and (a['previous_head'],a['end_head'])!=(b['previous_head'],b['end_head']):
                    conflicts.append({'kind':'CONFLICTING_RANGE','range':[a['start'],a['end']],'roots':[a['root'],b['root']]})
                elif a['end']==b['end'] and a['end_head']!=b['end_head']:
                    conflicts.append({'kind':'CONFLICTING_END','end':a['end'],'roots':[a['root'],b['root']]})
                elif a['start']==b['end']+1 and a['previous_head']!=b['end_head']:
                    conflicts.append({'kind':'BROKEN_RANGE_LINK','roots':[b['root'],a['root']]})
                elif b['start']==a['end']+1 and b['previous_head']!=a['end_head']:
                    conflicts.append({'kind':'BROKEN_RANGE_LINK','roots':[a['root'],b['root']]})
        # Anchor to the actual local scheduler log when provided: commitments cannot
        # silently disagree with the known sequence boundaries.
        mismatched=[]
        if scheduler is not None:
            if not validate_scheduler(scheduler):rejected.append('INVALID_LOCAL_SCHEDULER')
            else:
                for b in accepted:
                    if b['end']>len(scheduler) or b['previous_head']!=(scheduler[b['start']-2]['head'] if b['start']>1 else ZERO) or b['end_head']!=scheduler[b['end']-1]['head']:
                        mismatched.append({'root':b['root'],'range':[b['start'],b['end']]})
        covered=set()
        for b in accepted:covered.update(range(b['start'],b['end']+1))
        declared_end=self.expected_end if self.expected_end is not None else max((b['end'] for b in accepted),default=0)
        missing=[i for i in range(1,declared_end+1) if i not in covered]
        suffix=max((b['end'] for b in accepted),default=0)<declared_end
        if conflicts:status='CONFLICTING_COMMITMENTS'
        elif mismatched:status='LOCAL_LOG_MISMATCH'
        elif missing:status='TRUNCATED_OR_MISSING_RANGE' if suffix else 'SELECTIVE_SUPPRESSION'
        elif rejected:status='INVALID_RECEIPTS'
        elif independent_claims<3:status='INSUFFICIENT_DECLARED_CUSTODY'
        else:status='MATCHED_FIXTURE_CUSTODY'
        result={'version':'JANE-163','status':status,'accepted':len(accepted),'rejected':rejected,
                'claimed_independent_admins':independent_claims,'real_independence_verified':False,
                'conflicts':conflicts,'local_log_mismatches':mismatched,'missing_sequences':missing,
                'suffix_truncation':suffix,'expected_end':declared_end,'active_parent':'FROZEN',
                'jane_learning_applied':False,'scope':'local fixture with configured operator claims'}
        result['digest']=sha(result)
        self.observe(result)
        return result

def demo():
    records=scheduler_records(6)
    keys=[Ed25519PrivateKey.generate() for _ in range(3)]
    roots={f'root-{i}':Root(key_hex(keys[i]),f'admin-{i}') for i in range(3)}
    claims=[envelope(keys[i],checkpoint(records,1,6,f'root-{i}',f'admin-{i}',f'nonce-{i}')) for i in range(3)]
    auditor=Auditor(':memory:',roots,expected_end=6)
    matched=auditor.audit(claims,records)
    missing=auditor.audit(claims[:2],records)
    truncated=auditor.audit([envelope(keys[i],checkpoint(records,1,4,f'root-{i}',f'admin-{i}',f'truncated-{i}')) for i in range(3)],records)
    audit=auditor.chain_status();auditor.close()
    return {'matched':matched,'two_custodians':missing,'suffix_truncated':truncated,'ledger':audit,'tests':'run test_witness.py'}

if __name__=='__main__':print(json.dumps(demo(),indent=2))
