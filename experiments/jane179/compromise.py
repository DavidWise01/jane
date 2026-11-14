"""JANE 179 — compromise-aware signed authority with a separate recovery council.

Scope: deterministic fixture proof verification, not proof of actual key theft or
real-world administrative independence. All transitions are append-only.
"""
from __future__ import annotations
import hashlib, json, sqlite3
from dataclasses import dataclass
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def sha(x): return hashlib.sha256(canonical(x)).hexdigest()
def pub(priv): return priv.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex()
def sign(priv,payload): return priv.sign(canonical(payload)).hex()
def verify(key_hex,payload,sig_hex):
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(key_hex)).verify(bytes.fromhex(sig_hex),canonical(payload));return True
    except (ValueError,TypeError,Exception): return False

def key(seed):return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(seed.encode()).digest())

@dataclass(frozen=True)
class Policy:
    recovery_quorum:int=2
    max_future_skew:int=30
    def __post_init__(self):
        if self.recovery_quorum<2:raise ValueError('quorum too small')

class Registry:
    """SQLite append-only events, single authority key per identity at each epoch."""
    def __init__(self,db=':memory:',policy=Policy()):
        self.db=sqlite3.connect(str(db));self.db.execute('pragma foreign_keys=on');self.policy=policy
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,kind TEXT NOT NULL,data TEXT NOT NULL,prev TEXT NOT NULL,head TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS identities(name TEXT PRIMARY KEY,key TEXT NOT NULL,epoch INTEGER NOT NULL,compromised_from INTEGER,revoked INTEGER NOT NULL DEFAULT 0);
          CREATE TABLE IF NOT EXISTS stewards(name TEXT PRIMARY KEY,key TEXT NOT NULL,root TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS nonces(nonce TEXT PRIMARY KEY);
          CREATE TABLE IF NOT EXISTS grants(grant TEXT PRIMARY KEY,issuer TEXT NOT NULL,delegate TEXT NOT NULL,issued_at INTEGER NOT NULL,scope TEXT NOT NULL);
        ''');self.db.commit()
    def close(self):self.db.close()
    def _event(self,kind,data):
        n=self.db.execute('select count(*) from events').fetchone()[0]
        prior=self.db.execute('select head from events order by seq desc limit 1').fetchone()
        prev=prior[0] if prior else '0'*64
        content={'seq':n,'kind':kind,'data':data,'prev':prev};head=sha(content)
        self.db.execute('insert into events values(?,?,?,?,?)',(n,kind,json.dumps(data,sort_keys=True),prev,head))
    def audit(self,external_head=None):
        prev='0'*64
        for n,kind,data,p,h in self.db.execute('select seq,kind,data,prev,head from events order by seq'):
            if p!=prev or h!=sha({'seq':n,'kind':kind,'data':json.loads(data),'prev':p}):return 'TAMPERED'
            prev=h
        return 'EXTERNAL_HEAD_MISMATCH' if external_head is not None and external_head!=prev else 'VALID_LOCAL_CHAIN'
    def head(self):
        row=self.db.execute('select head from events order by seq desc limit 1').fetchone();return row[0] if row else '0'*64
    def enroll(self,name,key_hex):
        if not name or len(bytes.fromhex(key_hex))!=32:raise ValueError('identity')
        self.db.execute('insert into identities(name,key,epoch) values(?,?,0)',(name,key_hex));self._event('ENROLL',{'name':name,'key':key_hex});self.db.commit()
    def steward(self,name,key_hex,root):
        if not root:raise ValueError('root')
        self.db.execute('insert into stewards values(?,?,?)',(name,key_hex,root));self._event('STEWARD_FIXTURE',{'name':name,'root':root,'key':key_hex});self.db.commit()
    def decision(self,body,sig):
        """A signed action contains identity, key epoch, time, nonce, and scope."""
        try:
            name=body['identity'];timestamp=body['time'];nonce=body['nonce'];epoch=body['epoch']
            rec=self.db.execute('select key,epoch,compromised_from,revoked from identities where name=?',(name,)).fetchone()
            if not rec:return 'UNKNOWN_IDENTITY'
            k,current,cutoff,revoked=rec
            if revoked:return 'REVOKED'
            if epoch!=current:return 'OLD_KEY_EPOCH'
            if cutoff is not None:return 'COMPROMISED_KEY_QUARANTINED'
            if not verify(k,body,sig):return 'BAD_SIGNATURE'
            if self.db.execute('select 1 from nonces where nonce=?',(nonce,)).fetchone():return 'REPLAY'
            self.db.execute('insert into nonces values(?)',(nonce,));self._event('DECISION',{'body':body,'signature':sig});self.db.commit()
            return 'ACCEPTED_FIXTURE'
        except (KeyError,TypeError,sqlite3.Error):return 'INVALID_DECISION'
    def declare_compromise(self,identity,cutoff,reason,attestations,nonce,now):
        """Recovery council attests to a compromise boundary; source claims remain fixture assumptions."""
        rec=self.db.execute('select key,epoch,compromised_from from identities where name=?',(identity,)).fetchone()
        if not rec:return 'UNKNOWN_IDENTITY'
        if self.db.execute('select 1 from nonces where nonce=?',(nonce,)).fetchone():return 'REPLAY'
        if type(cutoff)!=int or cutoff>now+self.policy.max_future_skew:return 'INVALID_BOUNDARY'
        body={'kind':'COMPROMISE','identity':identity,'cutoff':cutoff,'reason':reason,'nonce':nonce}
        validation=self._council(body,attestations)
        if validation!='QUORUM_VERIFIED_FIXTURE':return validation
        if rec[2] is not None:return 'ALREADY_COMPROMISED'
        with self.db:
            self.db.execute('update identities set compromised_from=? where name=?',(cutoff,identity))
            self.db.execute('insert into nonces values(?)',(nonce,))
            self._event('COMPROMISE',{'claim':body,'attestations':attestations})
        return 'COMPROMISE_RECORDED'
    def _council(self,body,attestations):
        roots=set();names=set()
        for a in attestations:
            if not isinstance(a,dict) or not all(x in a for x in ('steward','signature')):return 'BAD_ATTESTATION'
            if a['steward'] in names:return 'DUPLICATE_STEWARD'
            names.add(a['steward'])
            row=self.db.execute('select key,root from stewards where name=?',(a['steward'],)).fetchone()
            if not row or not verify(row[0],body,a['signature']):return 'BAD_ATTESTATION'
            roots.add(row[1])
        return 'QUORUM_VERIFIED_FIXTURE' if len(roots)>=self.policy.recovery_quorum else 'INSUFFICIENT_DISTINCT_ROOTS'
    def recover(self,identity,new_key,epoch,at,nonce,attestations):
        row=self.db.execute('select key,epoch,compromised_from from identities where name=?',(identity,)).fetchone()
        if not row:return 'UNKNOWN_IDENTITY'
        if self.db.execute('select 1 from nonces where nonce=?',(nonce,)).fetchone():return 'REPLAY'
        if row[2] is None:return 'NOT_COMPROMISED'
        if epoch!=row[1]+1 or at<row[2] or new_key==row[0]:return 'INVALID_SUCCESSION'
        try:
            if len(bytes.fromhex(new_key))!=32:return 'INVALID_SUCCESSION'
        except ValueError:return 'INVALID_SUCCESSION'
        body={'kind':'RECOVERY','identity':identity,'old_epoch':row[1],'new_epoch':epoch,'new_key':new_key,'at':at,'nonce':nonce}
        validation=self._council(body,attestations)
        if validation!='QUORUM_VERIFIED_FIXTURE':return validation
        with self.db:
            self.db.execute('update identities set key=?,epoch=?,compromised_from=null where name=?',(new_key,epoch,identity))
            self.db.execute('insert into nonces values(?)',(nonce,))
            self._event('RECOVER',{'claim':body,'attestations':attestations,'previous_key':row[0]})
        return 'RECOVERED_SAME_IDENTITY'
    def grant(self,grant_id,issuer,delegate,scope,issued_at):
        row=self.db.execute('select compromised_from,revoked from identities where name=?',(issuer,)).fetchone()
        if not row:return 'UNKNOWN_ISSUER'
        if row[1] or row[0] is not None:return 'ISSUER_QUARANTINED'
        self.db.execute('insert into grants values(?,?,?,?,?)',(grant_id,issuer,delegate,issued_at,scope));self._event('GRANT',{'id':grant_id,'issuer':issuer,'delegate':delegate,'scope':scope,'time':issued_at});self.db.commit();return 'GRANT_RECORDED'
    def grant_status(self,grant_id):
        row=self.db.execute('select issuer,issued_at from grants where grant=?',(grant_id,)).fetchone()
        if not row:return 'UNKNOWN_GRANT'
        parent=self.db.execute('select compromised_from,revoked from identities where name=?',(row[0],)).fetchone()
        if parent[1]:return 'REVOKED'
        return 'REVIEW_COMPROMISED_LINEAGE' if parent[0] is not None else 'UNCHANGED_PENDING_REVIEW'

def council(privs,body):return [{'steward':name,'signature':sign(k,body)} for name,k in privs.items()]

def demo():
    r=Registry();original=key('original');nextkey=key('replacement')
    a=key('council-a');b=key('council-b')
    r.enroll('Jane-Steward',pub(original));r.steward('A',pub(a),'root-A');r.steward('B',pub(b),'root-B')
    history={'identity':'Jane-Steward','epoch':0,'time':90,'nonce':'old-1','scope':'calibration'}
    before=r.decision(history,sign(original,history))
    body={'kind':'COMPROMISE','identity':'Jane-Steward','cutoff':100,'reason':'fixture report','nonce':'c1'}
    compromise=r.declare_compromise('Jane-Steward',100,'fixture report',council({'A':a,'B':b},body),'c1',120)
    late={'identity':'Jane-Steward','epoch':0,'time':110,'nonce':'late-1','scope':'calibration'}
    quarantined=r.decision(late,sign(original,late))
    recovery={'kind':'RECOVERY','identity':'Jane-Steward','old_epoch':0,'new_epoch':1,'new_key':pub(nextkey),'at':121,'nonce':'r1'}
    recovered=r.recover('Jane-Steward',pub(nextkey),1,121,'r1',council({'A':a,'B':b},recovery))
    fresh={'identity':'Jane-Steward','epoch':1,'time':122,'nonce':'new-1','scope':'calibration'}
    accepted=r.decision(fresh,sign(nextkey,fresh))
    result={'experiment':'JANE-179','before':before,'compromise':compromise,'quarantined':quarantined,'recovery':recovered,'new_epoch_decision':accepted,'audit':r.audit(),'head':r.head(),'active_parent':'frozen','independence_verified':False,'physical_compromise_verified':False}
    r.close();return result
if __name__=='__main__':print(json.dumps(demo(),indent=2))