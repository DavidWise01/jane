"""JANE 174: reproducible acquisition with evidence and declared ancestry.

Fixture-scale verification; no physical instrument independence claims.
"""
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value)).hexdigest()


def key(seed):
    return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(seed.encode()).digest())


def signed(payload, signer, private):
    return {'payload': payload, 'signer': signer, 'signature': private.sign(canonical(payload)).hex()}


def verify(receipt, public_keys):
    try:
        public_keys[receipt['signer']].verify(bytes.fromhex(receipt['signature']), canonical(receipt['payload']))
        return True
    except (KeyError, ValueError, TypeError, InvalidSignature, AttributeError):
        return False


def acquisition(device, run, procedure, sample, value, roots, private, observed_at=1000):
    """Sample is bytes, not a mutable reference to a file."""
    body = {'device':device,'run':run,'procedure':procedure,'raw_sha256':digest(sample),
            'value_milli':value,'roots':list(roots),'observed_at':observed_at}
    return signed(body, device, private)


@dataclass(frozen=True)
class Policy:
    procedure: str
    tolerance_milli: int = 5
    max_age: int = 300
    required_roots: int = 2
    max_receipts: int = 32
    def __post_init__(self):
        if not self.procedure or any(type(v) is not int or v < 0 for v in (self.tolerance_milli,self.max_age)):
            raise ValueError('invalid policy')
        if not (2 <= self.required_roots <= 8) or not (2 <= self.max_receipts <= 128):
            raise ValueError('invalid budget')


class Ledger:
    """Hash-linked local journal. External retained head required to detect truncation."""
    def __init__(self,path=':memory:'):
        self.db=sqlite3.connect(str(path))
        self.db.execute('create table if not exists events(seq integer primary key, kind text not null, body text not null, prev text not null, head text not null)')
        self.db.execute('create table if not exists seen(device text, run text, raw text, primary key(device,run))')
        self.db.commit()

    def append(self,kind,body):
        seq,prev=self.db.execute('select count(*),coalesce((select head from events order by seq desc limit 1),?) from events',('0'*64,)).fetchone()
        row={'seq':seq,'kind':kind,'body':body,'prev':prev}
        head=digest(row)
        self.db.execute('insert into events values(?,?,?,?,?)',(seq,kind,canonical(body).decode(),prev,head))
        self.db.commit()
        return head

    def check(self,external_head=None):
        expected='0'*64
        rows=self.db.execute('select seq,kind,body,prev,head from events order by seq').fetchall()
        for pos,(seq,kind,body,prev,head) in enumerate(rows):
            if seq != pos or prev != expected or digest({'seq':seq,'kind':kind,'body':json.loads(body),'prev':prev}) != head:
                return 'JOURNAL_TAMPERED'
            expected=head
        if external_head is not None and external_head!=expected:
            return 'EXTERNAL_HEAD_MISMATCH'
        return 'VALID_LOCAL_CHAIN'

    def remember(self,device,run,raw):
        try:
            self.db.execute('insert into seen values(?,?,?)',(device,run,raw))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False


class FLAY:
    def __init__(self, keys, policy, ledger=None):
        self.keys=keys
        self.policy=policy
        self.ledger=ledger or Ledger()
        self.active='FROZEN_PARENT'

    def audit(self, receipts, blobs, now=1100):
        if not (2 <= len(receipts) <= self.policy.max_receipts):
            result=self._finish('INVALID_RECEIPT_COUNT',[],[],[])
            return result
        accepted=[];rejections=[]; seen_in_batch=set()
        for receipt in receipts:
            payload=receipt.get('payload',{}) if isinstance(receipt,dict) else {}
            device=payload.get('device')
            run=payload.get('run')
            rejection=None
            if not verify(receipt,self.keys) or receipt.get('signer')!=device:
                rejection='BAD_SIGNATURE'
            elif not isinstance(run,str) or not run or not isinstance(device,str):
                rejection='INVALID_IDENTITY'
            elif (device,run) in seen_in_batch:
                rejection='DUPLICATE_RUN'
            elif payload.get('procedure')!=self.policy.procedure:
                rejection='PROCEDURE_MISMATCH'
            elif type(payload.get('value_milli')) is not int:
                rejection='INVALID_VALUE'
            elif type(payload.get('observed_at')) is not int or not 0<=now-payload['observed_at']<=self.policy.max_age:
                rejection='STALE_OR_FUTURE'
            elif not isinstance(payload.get('roots'),list) or not payload['roots'] or any(not isinstance(r,str) or not r for r in payload['roots']) or len(set(payload['roots']))!=len(payload['roots']):
                rejection='INVALID_ANCESTRY'
            elif (device,run) not in blobs:
                rejection='RAW_UNAVAILABLE'
            elif digest(blobs[(device,run)])!=payload.get('raw_sha256'):
                rejection='RAW_COMMITMENT_MISMATCH'
            elif not self.ledger.remember(device,run,payload['raw_sha256']):
                rejection='REPLAY_RUN'
            if isinstance(device,str) and isinstance(run,str):
                seen_in_batch.add((device,run))
            if rejection:
                rejections.append({'device':device,'run':run,'reason':rejection})
                self.ledger.append('REJECT',{'device':device,'run':run,'reason':rejection})
            else:
                accepted.append(payload)
                self.ledger.append('ACCEPT',{'device':device,'run':run,'raw':payload['raw_sha256'],'roots':payload['roots']})

        status='INSUFFICIENT_VALID_ACQUISITIONS'
        support=[]
        if len(accepted)>=self.policy.required_roots:
            # Enforce pairwise disjoint, *declared* lineage and distinct devices.
            groups=sorted(accepted,key=lambda p:(p['device'],p['run']))
            best=[]
            def dfs(index, selected, used_roots, devices):
                nonlocal best
                if len(selected)>len(best):best=list(selected)
                if index==len(groups):return
                if len(selected)+len(groups)-index<=len(best):return
                p=groups[index];roots=set(p['roots'])
                if not used_roots.intersection(roots) and p['device'] not in devices:
                    dfs(index+1,selected+[p],used_roots|roots,devices|{p['device']})
                dfs(index+1,selected,used_roots,devices)
            dfs(0,[],set(),set())
            support=[{'device':p['device'],'run':p['run'],'roots':p['roots'],'value_milli':p['value_milli']} for p in best]
            if len(best)<self.policy.required_roots or len(best)<len(accepted):
                status='SHARED_ACQUISITION_ANCESTRY'
            elif max(p['value_milli'] for p in best)-min(p['value_milli'] for p in best)>self.policy.tolerance_milli:
                status='MEASUREMENT_DISAGREEMENT'
            elif rejections:
                status='REPRODUCED_WITH_REJECTIONS'
            else:
                status='REPRODUCED_DECLARED_FIXTURE'
        if not accepted and rejections:
            status='NO_VALID_ACQUISITIONS'
        return self._finish(status,accepted,rejections,support)

    def _finish(self,status,accepted,rejections,support):
        out={'experiment':'JANE-174','status':status,'policy':self.policy.__dict__,
             'valid_acquisitions':len(accepted),'rejected':rejections,'declared_independent_support':support,
             'learning_applied':False,'active':self.active,'physical_independence_verified':False,
             'scope':'signed local fixtures; no physical device or external custodian verification'}
        out['evidence_digest']=digest(out)
        out['local_head']=self.ledger.append('DECISION',{'status':status,'evidence_digest':out['evidence_digest']})
        return out


def example():
    keys={name:key(name+'-174') for name in ('A','B','C')}
    public={n:p.public_key() for n,p in keys.items()}
    p=Policy('capture-v1',tolerance_milli=5)
    samples={(n,n+'-001'): ('raw:'+n).encode() for n in keys}
    receipts=[acquisition(n,n+'-001','capture-v1',samples[(n,n+'-001')],value,['instrument-'+n],keys[n]) for n,value in (('A',1000),('B',1002),('C',999))]
    engine=FLAY(public,p)
    result=engine.audit(receipts,samples)
    return {'result':result,'ledger_check':engine.ledger.check(),'receipt_count':len(receipts)}

if __name__=='__main__':print(json.dumps(example(),indent=2))