"""JANE 177: evidence-carrying, signed policy succession and bounded authority.

Cryptographic authority is only relative to an explicitly configured local trust registry.
No activation, real-world independence, or external publication is inferred.
"""
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def sha(obj):
    return hashlib.sha256(canon(obj).encode()).hexdigest()


def keypair(label):
    """Reproducible LOCAL TEST fixture, not secret key management."""
    seed=hashlib.sha256(('JANE177-local-fixture:'+label).encode()).digest()
    key=Ed25519PrivateKey.from_private_bytes(seed)
    return key,key.public_key()


def sign(key,obj):
    return key.sign(canon(obj).encode()).hex()


def verify(pub,obj,sig):
    try:
        pub.verify(bytes.fromhex(sig),canon(obj).encode())
        return True
    except (ValueError,InvalidSignature,TypeError,AttributeError):
        return False


@dataclass(frozen=True)
class Authority:
    principal:str
    scopes:tuple
    valid_from:int
    valid_until:int
    public_key:Ed25519PublicKey
    ancestry:str


class Gate:
    """A local authorization verifier, NOT a policy execution/activation engine."""
    def __init__(self, db=':memory:', authority=(), now=200, frozen_policy=None):
        self.conn=sqlite3.connect(db)
        self.conn.execute('CREATE TABLE IF NOT EXISTS decisions (seq INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, data TEXT, prev TEXT, head TEXT)')
        self.conn.execute('CREATE TABLE IF NOT EXISTS nonces (principal TEXT, nonce TEXT, PRIMARY KEY(principal,nonce))')
        self.conn.execute('CREATE TABLE IF NOT EXISTS revisions (scope TEXT, parent TEXT, revision TEXT, PRIMARY KEY(scope,parent))')
        self.authorities={a.principal:a for a in authority}
        self.now=now
        self.frozen_policy=frozen_policy or dict(version='v1',scope='calibration.clock',tolerance=5)
        self.frozen_digest=sha(self.frozen_policy)
        self.active_digest=self.frozen_digest

    def record(self,kind,data):
        row=self.conn.execute('SELECT head FROM decisions ORDER BY seq DESC LIMIT 1').fetchone()
        prev=row[0] if row else '0'*64
        blob=dict(kind=kind,data=data,prev=prev)
        head=sha(blob)
        self.conn.execute('INSERT INTO decisions (kind,data,prev,head) VALUES (?,?,?,?)',(kind,canon(data),prev,head))
        self.conn.commit()
        return head

    def audit(self,external_head=None):
        prev='0'*64
        for kind,data,prior,head in self.conn.execute('SELECT kind,data,prev,head FROM decisions ORDER BY seq'):
            if prior!=prev or sha(dict(kind=kind,data=json.loads(data),prev=prior))!=head:
                return 'LEDGER_TAMPER'
            prev=head
        if external_head is not None and external_head!=prev:
            return 'EXTERNAL_HEAD_MISMATCH'
        return 'LOCAL_CHAIN_VALID'

    def evaluate(self,evidence,policy):
        if set(evidence)!= {'original','repeat','scope'}:raise ValueError('evidence shape')
        if evidence['scope']!=policy['scope']:raise ValueError('scope mismatch')
        return 'ACCEPT' if abs(evidence['original']-evidence['repeat'])<=policy['tolerance'] else 'REJECT'

    def propose(self,proposal,signature,nonce,evidence):
        """Proposal is immutable signed content; result never changes active policy."""
        required={'principal','scope','parent_digest','new_policy','effective_at','expires_at','reason','nonce'}
        if not isinstance(proposal,dict) or set(proposal)!=required:
            return self._reject('MALFORMED_PROPOSAL',proposal,evidence)
        identity=proposal['principal']
        if not isinstance(identity,str) or identity not in self.authorities:
            return self._reject('UNKNOWN_AUTHORITY',proposal,evidence)
        auth=self.authorities[identity]
        if not verify(auth.public_key,proposal,signature):
            return self._reject('INVALID_SIGNATURE',proposal,evidence)
        if nonce!=proposal['nonce'] or not isinstance(nonce,str) or not nonce or len(nonce)>128:
            return self._reject('NONCE_MISMATCH',proposal,evidence)
        if self.conn.execute('SELECT 1 FROM nonces WHERE principal=? AND nonce=?',(identity,nonce)).fetchone():
            return self._reject('REPLAY_NONCE',proposal,evidence)
        self.conn.execute('INSERT INTO nonces VALUES (?,?)',(identity,nonce))
        self.conn.commit() # a signed nonce cannot be retried even if its proposal is denied
        scope=proposal['scope']
        if scope not in auth.scopes:
            return self._reject('OUT_OF_SCOPE',proposal,evidence)
        if not(auth.valid_from<=self.now<=auth.valid_until):
            return self._reject('AUTHORITY_EXPIRED',proposal,evidence)
        if proposal['effective_at']>proposal['expires_at'] or proposal['effective_at']<auth.valid_from or proposal['expires_at']>auth.valid_until:
            return self._reject('BAD_TIME_RANGE',proposal,evidence)
        if self.now < proposal['effective_at']:
            return self._reject('NOT_YET_EFFECTIVE',proposal,evidence)
        if self.now > proposal['expires_at']:
            return self._reject('POLICY_EXPIRED',proposal,evidence)
        if proposal['parent_digest']!=self.frozen_digest:
            return self._reject('WRONG_PREDECESSOR',proposal,evidence)
        p=proposal['new_policy']
        if not isinstance(p,dict) or set(p)!={'version','scope','tolerance'} or p['scope']!=scope or type(p['tolerance']) is not int or not 0<=p['tolerance']<=1000 or not isinstance(p['version'],str):
            return self._reject('BAD_POLICY',proposal,evidence)
        if evidence['scope']!=scope:
            return self._reject('EVIDENCE_SCOPE_MISMATCH',proposal,evidence)
        revision=sha(proposal)
        existing=self.conn.execute('SELECT revision FROM revisions WHERE scope=? AND parent=?',(scope,self.frozen_digest)).fetchone()
        if existing and existing[0]!=revision:
            return self._reject('CONFLICTING_REVISION',proposal,evidence)
        if not existing:
            self.conn.execute('INSERT INTO revisions VALUES (?,?,?)',(scope,self.frozen_digest,revision))
            self.conn.commit()
        old=self.evaluate(evidence,self.frozen_policy)
        new=self.evaluate(evidence,p)
        result=dict(status='AUTHORIZED_REPLAY',principal=identity,authority_ancestry=auth.ancestry,
            scope=scope,evidence_digest=sha(evidence),parent_digest=self.frozen_digest,
            policy_digest=sha(p),revision_digest=revision,old_verdict=old,new_verdict=new,
            policy_induced_change=old!=new,active_policy=self.active_digest,
            policy_activated=False,independent_authority_verified=False)
        self.record('AUTHORIZED_REPLAY',result)
        return result

    def _reject(self,reason,proposal,evidence):
        result=dict(status=reason,proposal_digest=sha(proposal),evidence_digest=sha(evidence),
                    active_policy=self.active_digest,policy_activated=False)
        self.record('DENIED',result)
        return result


def demo():
    owner,pub=keypair('policy-steward')
    a=Authority('steward',('calibration.clock',),0,1000,pub,'fixture-admin-01')
    engine=Gate(authority=[a])
    evidence=dict(original=1000,repeat=1003,scope='calibration.clock')
    proposal=dict(principal='steward',scope='calibration.clock',parent_digest=engine.frozen_digest,
        new_policy=dict(version='v2',scope='calibration.clock',tolerance=2),
        effective_at=150,expires_at=300,reason='tighten declared comparator',nonce='demo-001')
    result=engine.propose(proposal,sign(owner,proposal),'demo-001',evidence)
    return engine,result

if __name__=='__main__':
    gate,result=demo()
    print(json.dumps({'result':result,'audit':gate.audit()},indent=2))
