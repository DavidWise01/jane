"""JANE 164: authenticated, separately retained checkpoint anchors.

Separate SQLite files model separate custody stores; fixture keys and admins do
NOT demonstrate independent real-world operators. All inputs are untrusted.
"""
from __future__ import annotations
import hashlib, json, sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

ZERO='0'*64

def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def sha(obj):return hashlib.sha256(canonical(obj)).hexdigest()
def public(key):return key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex()
def signed(key,body):return {'body':body,'signature':key.sign(canonical(body)).hex()}
def authentic(pub,body,sig):
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub)).verify(bytes.fromhex(sig),canonical(body))
        return True
    except (ValueError,InvalidSignature,TypeError,AttributeError):return False

def make_log(n=6):
    out=[];prev=ZERO
    for seq in range(1,n+1):
        event={'sequence':seq,'previous':prev,'enabled':['A','B'],'selected':'A' if seq%2 else 'B'}
        head=sha(event);out.append({**event,'head':head});prev=head
    return out

def verify_log(records):
    if not isinstance(records,list):return False
    prev=ZERO
    for seq,event in enumerate(records,1):
        if not isinstance(event,dict) or set(event)!={'sequence','previous','enabled','selected','head'}:return False
        if type(event['sequence']) is not int or event['sequence']!=seq or event['previous']!=prev:return False
        if not isinstance(event['enabled'],list) or not all(isinstance(x,str) for x in event['enabled']):return False
        if not isinstance(event['selected'],str) or event['selected'] not in event['enabled']:return False
        if event['head']!=sha({k:v for k,v in event.items() if k!='head'}):return False
        prev=event['head']
    return True

def commitment(records,root,admin,nonce):
    if not verify_log(records) or not records:raise ValueError('invalid log')
    if not all(isinstance(x,str) and x for x in (root,admin,nonce)):raise ValueError('invalid identity')
    return {'protocol':'JANE-164','root':root,'admin':admin,'sequence':len(records),
            'head':records[-1]['head'],'genesis':ZERO,'nonce':nonce,
            'chronos':'2026-11-13T20:50:00-06:00'}

@dataclass(frozen=True)
class Custodian:
    public_key:str
    admin:str

class AnchorStore:
    """A fixture custody database independent of returned local-log SQLite."""
    def __init__(self,path,trust):
        self.db=sqlite3.connect(str(path))
        self.trust=trust
        self.db.execute('CREATE TABLE IF NOT EXISTS anchors(root TEXT, seq INTEGER, head TEXT, nonce TEXT, body TEXT, signature TEXT, PRIMARY KEY(root,seq), UNIQUE(root,nonce))')
        self.db.commit()
    def close(self):self.db.close()
    def retain(self,receipt):
        try:
            body=receipt['body']; sig=receipt['signature'];root=body['root'];cfg=self.trust[root]
            if set(body)!={'protocol','root','admin','sequence','head','genesis','nonce','chronos'}:return 'INVALID_CLAIM'
            if body['protocol']!='JANE-164' or body['admin']!=cfg.admin or body['genesis']!=ZERO:return 'INVALID_CLAIM'
            if type(body['sequence']) is not int or body['sequence']<1:return 'INVALID_CLAIM'
            if not isinstance(body['nonce'],str) or not body['nonce']:return 'INVALID_CLAIM'
            if not isinstance(body['chronos'],str) or not body['chronos']:return 'INVALID_CLAIM'
            if not isinstance(body['head'],str) or len(body['head'])!=64 or any(c not in '0123456789abcdef' for c in body['head']):return 'INVALID_CLAIM'
            if not authentic(cfg.public_key,body,sig):return 'BAD_SIGNATURE'
            existing=self.db.execute('SELECT head FROM anchors WHERE root=? AND seq=?',(root,body['sequence'])).fetchone()
            if existing:return 'DUPLICATE' if existing[0]==body['head'] else 'SIGNED_FORK'
            highest=self.db.execute('SELECT max(seq) FROM anchors WHERE root=?',(root,)).fetchone()[0]
            if highest is not None and body['sequence']<highest:return 'STALE_ANCHOR'
            try:
                self.db.execute('INSERT INTO anchors VALUES(?,?,?,?,?,?)',(root,body['sequence'],body['head'],body['nonce'],canonical(body).decode(),sig));self.db.commit()
            except sqlite3.IntegrityError:return 'REPLAY_NONCE'
            return 'RETAINED'
        except (KeyError,TypeError,ValueError):return 'INVALID_CLAIM'
    def receipts(self):
        return [{'body':json.loads(body),'signature':sig} for body,sig in self.db.execute('SELECT body,signature FROM anchors ORDER BY root,seq')]

def audit(returned_log,receipts,trust,minimum_distinct_admins=2):
    """Validate returned history against trusted, separately obtained receipts.

    An anchored history may be extended, but only with an intact prefix. Unknown
    present-day completeness cannot be asserted without an expected latest anchor.
    """
    if not verify_log(returned_log):return {'status':'LOCAL_LOG_TAMPERED','accepted':False}
    by_root={};adms={};failures=[];validated=[]
    for item in receipts:
        try:
            body=item['body'];root=body['root'];config=trust[root]
            if body.get('protocol')!='JANE-164' or body.get('admin')!=config.admin or body.get('genesis')!=ZERO or type(body.get('sequence')) is not int or body['sequence']<1 or not isinstance(body.get('head'),str) or len(body['head'])!=64 or not isinstance(body.get('nonce'),str) or not body['nonce'] or not isinstance(body.get('chronos'),str) or not body['chronos']:raise ValueError('INVALID_CLAIM')
            if not authentic(config.public_key,body,item['signature']):raise ValueError('BAD_SIGNATURE')
            by_root.setdefault(root,[]).append(body);adms[root]=config.admin;validated.append(body)
        except (KeyError,TypeError,ValueError) as exc:failures.append(str(exc) if str(exc) else 'INVALID_RECEIPT')
    if failures:return {'status':'UNTRUSTED_ANCHOR','accepted':False,'failures':failures}
    if not validated:return {'status':'ANCHOR_UNAVAILABLE','accepted':False}
    for root,claims in by_root.items():
        seqs={};nonces=set()
        for claim in claims:
            if claim['nonce'] in nonces:return {'status':'ANCHOR_REPLAY','accepted':False}
            nonces.add(claim['nonce'])
            old=seqs.get(claim['sequence'])
            if old is not None and old!=claim['head']:return {'status':'SIGNED_FORK','accepted':False}
            seqs[claim['sequence']]=claim['head']
    by_seq={}
    for body in validated:
        seq=body['sequence'];by_seq.setdefault(seq,set()).add(body['head'])
        if seq>len(returned_log):return {'status':'CLEAN_SUFFIX_TRUNCATION','accepted':False,'expected_end':seq,'returned_end':len(returned_log)}
        if returned_log[seq-1]['head']!=body['head']:return {'status':'ANCHORED_HISTORY_MISMATCH','accepted':False,'sequence':seq}
    if any(len(heads)>1 for heads in by_seq.values()):return {'status':'SIGNED_FORK','accepted':False}
    groups={admin for admin in adms.values()}
    if len(groups)<minimum_distinct_admins:return {'status':'SHARED_ADMINISTRATION','accepted':False,'claimed_roots':len(by_root)}
    last=max(by_seq)
    return {'status':'VALID_EXTENSION' if len(returned_log)>last else 'ANCHORED_MATCH',
            'accepted':True,'claimed_roots':len(by_root),'declared_admins':len(groups),
            'highest_anchored_sequence':last,'returned_end':len(returned_log),
            'independent_operators_verified':False,'physical_execution_verified':False,
            'jane_activation':False}

def fixture():
    keys={n:Ed25519PrivateKey.from_private_bytes(bytes([i])*32) for i,n in enumerate('ABC',1)}
    trust={n:Custodian(public(k),'admin-'+n) for n,k in keys.items()}
    log=make_log(6)
    receipts=[signed(k,commitment(log,n,trust[n].admin,'nonce-'+n)) for n,k in keys.items()]
    return log,receipts,trust,keys

if __name__=='__main__':
    log,r,t,k=fixture();print(json.dumps({'result':audit(log,r,t),'truncated':audit(log[:4],r,t),'extension':audit(make_log(8),r,t)},indent=2))