"""JANE 165: authenticated checkpoint freshness without claiming global completeness.

This is a bounded, offline verification demonstration. Wall-clock freshness depends on
an externally trusted observation time. The local fixture keys aren't independent operators.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def sha(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


@dataclass(frozen=True)
class Policy:
    max_age: int = 300
    future_skew: int = 30
    quorum: int = 3
    def __post_init__(self):
        for x in (self.max_age, self.future_skew, self.quorum):
            if type(x) is not int or x < 0:
                raise ValueError('invalid policy')
        if self.max_age > 86400 * 30 or self.future_skew > 86400 or self.quorum < 1 or self.quorum > 16:
            raise ValueError('unreasonable policy')


def make_receipt(key, root, administrator, sequence, head, observed_at, nonce):
    payload = dict(root=root, administrator=administrator, sequence=sequence, head=head,
                   observed_at=observed_at, nonce=nonce, protocol='JANE165')
    return dict(payload=payload, signature=key.sign(canonical(payload)).hex())


class CustodyClock:
    """Persistent seen-nonce and highest-sequence audit across process restarts."""
    def __init__(self, db=':memory:'):
        self.con = sqlite3.connect(db)
        self.con.execute('CREATE TABLE IF NOT EXISTS receipts (root TEXT, nonce TEXT, sequence INTEGER, head TEXT, observed INTEGER, PRIMARY KEY(root,nonce))')
        self.con.execute('CREATE TABLE IF NOT EXISTS highwater (root TEXT PRIMARY KEY, sequence INTEGER, head TEXT)')
        self.con.commit()
    def check_and_store(self, payload):
        root, nonce, seq, head = (payload[k] for k in ('root','nonce','sequence','head'))
        with self.con:
            if self.con.execute('SELECT 1 FROM receipts WHERE root=? AND nonce=?',(root,nonce)).fetchone():
                return 'REPLAY'
            old = self.con.execute('SELECT sequence,head FROM highwater WHERE root=?',(root,)).fetchone()
            if old and seq < old[0]: return 'ROLLBACK'
            if old and seq == old[0] and head != old[1]: return 'SIGNED_FORK'
            self.con.execute('INSERT INTO receipts VALUES (?,?,?,?,?)',(root,nonce,seq,head,payload['observed_at']))
            if not old or seq > old[0]:
                self.con.execute('INSERT OR REPLACE INTO highwater VALUES (?,?,?)',(root,seq,head))
        return 'RECORDED'
    def close(self):
        if self.con is not None:
            self.con.close()
            self.con = None
    def __del__(self): self.close()


class FLAY165:
    def __init__(self, trusted, policy, db=':memory:'):
        """trusted: root -> (public_key, administrator). This is configured trust, not proof of independent operation."""
        self.trusted=trusted
        self.policy=policy
        self.store=CustodyClock(db)
        self.events=[]
        self.active_parent='frozen_parent'
    def _append(self, result):
        event=dict(sequence=len(self.events),previous=self.events[-1]['digest'] if self.events else '0'*64,result=result)
        event['digest']=sha(event)
        self.events.append(event)
    def verify_one(self, receipt, now):
        if type(now) is not int or now < 0: raise ValueError('untrusted observation clock')
        if not isinstance(receipt,dict) or set(receipt)!={'payload','signature'}: return 'BAD_FORMAT',None
        p=receipt['payload']; sign=receipt['signature']
        if not isinstance(p,dict) or set(p)!={'root','administrator','sequence','head','observed_at','nonce','protocol'}:
            return 'BAD_FORMAT',None
        if p['protocol']!='JANE165' or not isinstance(p['root'],str) or not isinstance(p['administrator'],str) or not isinstance(p['nonce'],str) or not p['nonce'] or len(p['nonce'])>128:
            return 'BAD_FORMAT',None
        if type(p['sequence']) is not int or p['sequence']<0 or type(p['observed_at']) is not int or p['observed_at']<0:
            return 'BAD_FORMAT',None
        if not isinstance(p['head'],str) or len(p['head'])!=64 or any(c not in '0123456789abcdef' for c in p['head']):
            return 'BAD_FORMAT',None
        if not isinstance(sign,str) or len(sign)!=128: return 'BAD_SIGNATURE',None
        trusted=self.trusted.get(p['root'])
        if trusted is None: return 'UNKNOWN_ROOT',None
        key,admin=trusted
        if p['administrator']!=admin: return 'ADMIN_MISMATCH',None
        try: key.verify(bytes.fromhex(sign),canonical(p))
        except (InvalidSignature,ValueError): return 'BAD_SIGNATURE',None
        age=now-p['observed_at']
        # A valid signature is historical evidence even when not eligible for current authorization.
        freshness='FUTURE_CLOCK' if age < -self.policy.future_skew else 'STALE_HISTORY' if age>self.policy.max_age else 'FRESH_HISTORY'
        record=self.store.check_and_store(p)
        if record!='RECORDED': return record,dict(payload=p,age=age,freshness=freshness)
        return freshness,dict(payload=p,age=age,freshness=freshness)
    def evaluate(self, receipts, now, local_sequence, local_head):
        if type(local_sequence) is not int or local_sequence<0 or not isinstance(local_head,str) or len(local_head)!=64:
            raise ValueError('local checkpoint')
        rows=[]; usable=[]; rooted={}; admins={}
        for receipt in receipts:
            status,info=self.verify_one(receipt,now)
            rows.append(dict(status=status,root=receipt.get('payload',{}).get('root') if isinstance(receipt,dict) else None))
            if info is None or status not in ('FRESH_HISTORY','STALE_HISTORY'):continue
            p=info['payload'];r=p['root'];a=p['administrator']
            if r in rooted or a in admins:
                rows[-1]['status']='DUPLICATE_CUSTODY'
                continue
            rooted[r]=p;admins[a]=r;usable.append((p,status))
        fresh=[p for p,status in usable if status=='FRESH_HISTORY']
        all_valid=[p for p,status in usable]
        # Check agreement separately from freshness, preserving conflicting evidence.
        heads={(p['sequence'],p['head']) for p in all_valid}
        if len(heads)>1: decision='CONFLICTING_CHECKPOINTS'
        elif len(fresh)>=self.policy.quorum and len({p['administrator'] for p in fresh})>=self.policy.quorum:
            unique={(p['sequence'],p['head']) for p in fresh}
            if len(unique)!=1:decision='CONFLICTING_CHECKPOINTS'
            elif next(iter(unique))!=(local_sequence,local_head):decision='LOCAL_HEAD_MISMATCH'
            else:decision='FRESH_FIXTURE_QUORUM_NO_COMPLETENESS_PROOF'
        elif len(all_valid)>=self.policy.quorum and len(heads)==1:
            decision='AUTHENTIC_HISTORIC_ONLY'
        else:decision='INSUFFICIENT_FRESH_CUSTODY'
        result=dict(version='JANE-165',decision=decision,rows=rows,now=now,policy=self.policy.__dict__,
                    signed_checkpoint_count=len(all_valid),fresh_count=len(fresh),
                    local_head=local_head,local_sequence=local_sequence,
                    independence_verified=False,global_completeness_verified=False,
                    active_parent=self.active_parent,learning_applied=False,
                    caveat='Configured fixture administrators and caller-supplied clock are not independent external evidence')
        result['digest']=sha(result)
        self._append(dict(result_digest=result['digest'],decision=decision))
        return result
    def audit(self, external_head=None):
        prior='0'*64
        for n,event in enumerate(self.events):
            if event['sequence']!=n or event['previous']!=prior or sha({k:v for k,v in event.items() if k!='digest'})!=event['digest']:
                return 'LOCAL_LEDGER_TAMPERED'
            prior=event['digest']
        return 'EXTERNAL_HEAD_MISMATCH' if external_head is not None and prior!=external_head else 'VALID_LOCAL_CHAIN'


def fixture():
    keys=[Ed25519PrivateKey.from_private_bytes(hashlib.sha256(f'jane165 fixture root {i}'.encode()).digest()) for i in range(3)]
    trusted={f'fixture-{i}':(k.public_key(),f'admin-{i}') for i,k in enumerate(keys)}
    h='ab'*32
    return keys,trusted,h


def demo():
    keys,trusted,head=fixture();now=1700000300
    fresh=[make_receipt(k,f'fixture-{i}',f'admin-{i}',6,head,now-10,f'nonce-{i}') for i,k in enumerate(keys)]
    stale=[make_receipt(k,f'fixture-{i}',f'admin-{i}',6,head,now-1000,f'stale-{i}') for i,k in enumerate(keys)]
    a=FLAY165(trusted,Policy());f=a.evaluate(fresh,now,6,head)
    b=FLAY165(trusted,Policy());s=b.evaluate(stale,now,6,head)
    return dict(fresh=f,stale=s,ledger_a=a.audit(),ledger_b=b.audit())

if __name__=='__main__':print(json.dumps(demo(),indent=2))
