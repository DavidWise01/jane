"""JANE 178 — bounded, signed authority delegation. Synthetic fixture trust roots."""
import hashlib, json, sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def digest(x): return hashlib.sha256(canonical(x)).hexdigest()
def public_hex(key): return key.public_key().public_bytes_raw().hex()

@dataclass(frozen=True)
class Grant:
    grant_id:str
    issuer:str
    subject:str
    scopes:tuple
    start:int
    end:int
    depth:int
    parent:str
    nonce:str
    signature:str
    def payload(self): return {k:getattr(self,k) for k in ('grant_id','issuer','subject','scopes','start','end','depth','parent','nonce')}
    def as_dict(self): return {**self.payload(),'signature':self.signature}

def sign_grant(key,**kwargs):
    data=dict(kwargs); data['scopes']=tuple(sorted(set(data['scopes'])))
    unsigned={k:data[k] for k in ('grant_id','issuer','subject','scopes','start','end','depth','parent','nonce')}
    return Grant(**unsigned,signature=key.sign(canonical(unsigned)).hex())

class Authority:
    def __init__(self,db=':memory:',root_keys=None,root_scopes=('calibration','sensor'),start=0,end=100,depth=4):
        self.db=sqlite3.connect(db)
        self.db.execute('CREATE TABLE IF NOT EXISTS grants (id TEXT PRIMARY KEY, body TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS nonces (issuer TEXT NOT NULL, nonce TEXT NOT NULL, PRIMARY KEY(issuer,nonce))')
        self.db.execute('CREATE TABLE IF NOT EXISTS revocations (id TEXT PRIMARY KEY, ts INTEGER NOT NULL, issuer TEXT NOT NULL, sig TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY, prev TEXT NOT NULL, body TEXT NOT NULL, head TEXT NOT NULL)')
        self.keys=dict(root_keys or {})
        self.root_scopes=frozenset(root_scopes);self.start=start;self.end=end;self.depth=depth
        self.active_parent='frozen_parent'
    def register(self,identity,pub):
        if identity in self.keys and self.keys[identity]!=pub: raise ValueError('IDENTITY_KEY_CONFLICT')
        self.keys[identity]=pub
    def _log(self,kind,details):
        row=self.db.execute('SELECT seq,head FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
        seq=row[0]+1 if row else 0;prev=row[1] if row else '0'*64
        body=canonical({'kind':kind,'details':details}).decode();head=digest({'seq':seq,'prev':prev,'body':body})
        self.db.execute('INSERT INTO audit VALUES (?,?,?,?)',(seq,prev,body,head));self.db.commit()
    def audit(self,external_head=None):
        prior='0'*64
        for i,(seq,prev,body,head) in enumerate(self.db.execute('SELECT * FROM audit ORDER BY seq')):
            if seq!=i or prev!=prior or head!=digest({'seq':seq,'prev':prev,'body':body}):return 'AUDIT_TAMPERED'
            prior=head
        return 'EXTERNAL_HEAD_MISMATCH' if external_head is not None and external_head!=prior else 'VALID_LOCAL_CHAIN'
    def _verify(self,identity,payload,sig):
        if identity not in self.keys:return False
        try:
            Ed25519PublicKey.from_public_bytes(bytes.fromhex(self.keys[identity])).verify(bytes.fromhex(sig),canonical(payload))
            return True
        except (InvalidSignature,ValueError,TypeError):return False
    def stored(self,id):
        row=self.db.execute('SELECT body FROM grants WHERE id=?',(id,)).fetchone()
        return Grant(**json.loads(row[0])) if row else None
    def _chain(self,id,at,seen=None):
        seen=set() if seen is None else seen
        if id in seen:return ('CYCLE',None)
        seen.add(id)
        if id=='ROOT':
            if not self.start<=at<=self.end:return ('ROOT_EXPIRED',None)
            return ('OK',{'subject':'ROOT','scopes':self.root_scopes,'start':self.start,'end':self.end,'depth':self.depth})
        grant=self.stored(id)
        if grant is None:return ('MISSING_PARENT',None)
        if not self._verify(grant.issuer,grant.payload(),grant.signature):return ('BAD_ANCESTRY_SIGNATURE',None)
        if not grant.start<=at<=grant.end:return ('EXPIRED_ANCESTRY',None)
        if self.db.execute('SELECT 1 FROM revocations WHERE id=? AND ts<=?',(id,at)).fetchone():return ('REVOKED',None)
        status,parent=self._chain(grant.parent,at,seen)
        if status!='OK':return (status,None)
        if parent['subject']!=grant.issuer:return ('ISSUER_MISMATCH',None)
        if not set(grant.scopes)<=parent['scopes'] or grant.start<parent['start'] or grant.end>parent['end'] or grant.depth>=parent['depth'] or grant.depth<0:
            return ('ESCALATION',None)
        return ('OK',{'subject':grant.subject,'scopes':frozenset(grant.scopes),'start':grant.start,'end':grant.end,'depth':grant.depth})
    def enroll(self,grant,at):
        if not isinstance(grant,Grant):return 'INVALID_GRANT'
        p=grant.payload()
        if not grant.grant_id or not grant.nonce or grant.issuer==grant.subject:return 'INVALID_GRANT'
        if not grant.scopes or any(not isinstance(s,str) or not s for s in grant.scopes):return 'INVALID_SCOPE'
        if not all(type(i) is int for i in (grant.start,grant.end,grant.depth,at)) or grant.start>grant.end:return 'INVALID_INTERVAL'
        if not self._verify(grant.issuer,p,grant.signature):return 'BAD_SIGNATURE'
        status,par=self._chain(grant.parent,at)
        if status!='OK':return status
        if par['subject']!=grant.issuer:return 'ISSUER_MISMATCH'
        if not grant.start<=at<=grant.end:return 'NOT_EFFECTIVE'
        if grant.start<par['start'] or grant.end>par['end'] or not set(grant.scopes)<=par['scopes'] or grant.depth>=par['depth'] or grant.depth<0:return 'ESCALATION'
        if self.stored(grant.grant_id):return 'GRANT_ID_REPLAY'
        if self.db.execute('SELECT 1 FROM nonces WHERE issuer=? AND nonce=?',(grant.issuer,grant.nonce)).fetchone():return 'NONCE_REPLAY'
        # Forbid a descendant granting a different authority route back to an ancestor.
        cursor=grant.parent
        while cursor!='ROOT':
            node=self.stored(cursor)
            if node is None:break
            if node.issuer==grant.subject or node.subject==grant.subject:return 'IDENTITY_CYCLE'
            cursor=node.parent
        with self.db:
            self.db.execute('INSERT INTO grants VALUES (?,?)',(grant.grant_id,json.dumps(grant.as_dict(),sort_keys=True)))
            self.db.execute('INSERT INTO nonces VALUES (?,?)',(grant.issuer,grant.nonce))
        self._log('GRANT',{'id':grant.grant_id,'hash':digest(p)})
        return 'GRANT_ACCEPTED'
    def revoke(self,grant_id,issuer,at,key):
        grant=self.stored(grant_id)
        if grant is None:return 'UNKNOWN_GRANT'
        if issuer!=grant.issuer:return 'REVOCATION_UNAUTHORIZED'
        if self.db.execute('SELECT 1 FROM revocations WHERE id=?',(grant_id,)).fetchone():return 'ALREADY_REVOKED'
        payload={'grant_id':grant_id,'issuer':issuer,'at':at}
        signature=key.sign(canonical(payload)).hex()
        if not self._verify(issuer,payload,signature):return 'BAD_REVOCATION_SIGNATURE'
        with self.db:self.db.execute('INSERT INTO revocations VALUES (?,?,?,?)',(grant_id,at,issuer,signature))
        self._log('REVOKE',payload)
        return 'REVOKED'
    def authorize(self,grant_id,subject,scope,at):
        status,claims=self._chain(grant_id,at)
        if status!='OK':return status
        if claims['subject']!=subject or scope not in claims['scopes']:return 'SCOPE_DENIED'
        return 'AUTHORIZED_FIXTURE'

def demo():
    root=Ed25519PrivateKey.generate();alice=Ed25519PrivateKey.generate();bob=Ed25519PrivateKey.generate()
    a=Authority(root_keys={'ROOT':public_hex(root)},root_scopes=('sensor','calibration'),depth=3)
    a.register('alice',public_hex(alice));a.register('bob',public_hex(bob))
    g1=sign_grant(root,grant_id='g1',issuer='ROOT',subject='alice',scopes=('calibration',),start=10,end=80,depth=2,parent='ROOT',nonce='n1')
    g2=sign_grant(alice,grant_id='g2',issuer='alice',subject='bob',scopes=('calibration',),start=20,end=60,depth=1,parent='g1',nonce='n2')
    output={'parent':a.enroll(g1,25),'child':a.enroll(g2,25),'authorized':a.authorize('g2','bob','calibration',30),'revoked':a.revoke('g1','ROOT',40,root),'after_revoke':a.authorize('g2','bob','calibration',41),'audit':a.audit(),'active_parent':a.active_parent,'real_world_authority_verified':False}
    a.db.close()
    return output
if __name__=='__main__':print(json.dumps(demo(),indent=2))
