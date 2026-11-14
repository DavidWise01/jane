"""JANE 187: Signed watermark != demonstrated sequence coverage.

A bounded, offline cryptographic fixture. A complete inbox snapshot is checked
against a size-bound Merkle root and signed sender manifest. This does NOT prove
physical delivery, completeness of a remote store, or custodian independence.
"""
from __future__ import annotations
import hashlib, json, sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

MAX_ITEMS=256

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def hashof(x):return hashlib.sha256(canonical(x)).hexdigest()
def sign(key,body):return key.sign(canonical(body)).hex()
def verify(key,body,sig):
    try:key.verify(bytes.fromhex(sig),canonical(body));return True
    except (InvalidSignature,ValueError,TypeError):return False

def leaf_hash(x):return hashlib.sha256(b'J187:leaf:'+canonical(x)).digest()
def tree_root(items):
    if len(items)>MAX_ITEMS:raise ValueError('oversized snapshot')
    nodes=[leaf_hash(i) for i in items]
    if not nodes:return hashlib.sha256(b'J187:empty').hexdigest()
    while len(nodes)>1:
        nodes=[hashlib.sha256(b'J187:node:'+nodes[i]+(nodes[i+1] if i+1<len(nodes) else nodes[i])).digest() for i in range(0,len(nodes),2)]
    return nodes[0].hex()
def commitment(items):return hashof({'domain':'JANE187:tree:size-bound:v1','count':len(items),'root':tree_root(items)})

@dataclass(frozen=True)
class Signed:
    body:dict
    signature:str
    @classmethod
    def issue(cls,key,body):return cls(body,sign(key,body))

class Ledger:
    def __init__(self,path=':memory:'):
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS nonce (issuer TEXT, nonce TEXT, PRIMARY KEY(issuer,nonce))')
        self.db.execute('CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY,prev TEXT,body TEXT,head TEXT)')
        self.db.commit()
    def append(self,body):
        prev=self.db.execute('SELECT head FROM audit ORDER BY id DESC LIMIT 1').fetchone()
        prev=prev[0] if prev else '0'*64
        head=hashof({'prev':prev,'body':body})
        self.db.execute('INSERT INTO audit(prev,body,head) VALUES(?,?,?)',(prev,canonical(body).decode(),head));self.db.commit()
    def reserve(self,issuer,nonce):
        try:self.db.execute('INSERT INTO nonce VALUES (?,?)',(issuer,nonce));self.db.commit();return True
        except sqlite3.IntegrityError:return False
    def check(self):
        prev='0'*64
        for a,b,c in self.db.execute('SELECT prev,body,head FROM audit ORDER BY id'):
            if a!=prev or hashof({'prev':a,'body':json.loads(b)})!=c:return False
            prev=c
        return True
    def close(self):self.db.close()

class FLAY:
    def __init__(self,send_key,receive_key,path=':memory:'):
        self.sender=send_key;self.receiver=receive_key;self.ledger=Ledger(path)
        self.active='frozen_parent'
    def audit(self,sender_manifest:Signed,watermark:Signed,receipts:list[Signed],now:int=1000):
        # Validation never trusts unauthenticated metadata from the relay.
        s,w=sender_manifest.body,watermark.body
        if not verify(self.sender,s,sender_manifest.signature):return self._record('BAD_SENDER_SIGNATURE',{})
        if not verify(self.receiver,w,watermark.signature):return self._record('BAD_WATERMARK_SIGNATURE',{})
        if s.get('domain')!='JANE187:sender:v1' or w.get('domain')!='JANE187:watermark:v1':return self._record('BAD_DOMAIN',{})
        start,end=s.get('start'),s.get('end')
        if type(start)!=int or type(end)!=int or start<1 or end<start or end-start>=MAX_ITEMS:return self._record('INVALID_RANGE',{})
        if w.get('sender_digest')!=hashof(s) or w.get('through')!=end or w.get('start')!=start:return self._record('WATERMARK_SCOPE_MISMATCH',{})
        if type(w.get('issued_at'))!=int or abs(now-w['issued_at'])>300:return self._record('STALE_OR_FUTURE_WATERMARK',{})
        if not isinstance(w.get('nonce'),str) or not w['nonce']:return self._record('INVALID_NONCE',{})
        if len(receipts)>MAX_ITEMS:return self._record('OVERSIZED',{})
        # Validate all signatures and identities BEFORE comparing coverage.
        entries=[];by_seq={};bad=[]
        for receipt in receipts:
            r=receipt.body
            if not verify(self.receiver,r,receipt.signature):bad.append('BAD_ACK_SIGNATURE');continue
            if r.get('domain')!='JANE187:ack:v1' or r.get('sender_digest')!=hashof(s):bad.append('BAD_ACK_CONTEXT');continue
            n=r.get('seq')
            if type(n)!=int or n<start or n>end:bad.append('OUT_OF_RANGE_ACK');continue
            if n in by_seq:
                bad.append('CONFLICTING_ACK' if by_seq[n]!=r else 'DUPLICATE_ACK')
            else:by_seq[n]=r
            entries.append(r)
        if bad:return self._record(sorted(bad)[0],{'errors':sorted(set(bad))})
        # The checkpoint commits to the exact presented snapshot, including order.
        claimed_count=w.get('count'); claimed_root=w.get('inbox_commitment')
        if type(claimed_count)!=int or claimed_count<0 or claimed_count>MAX_ITEMS:return self._record('INVALID_COMMITMENT_SIZE',{})
        if claimed_count!=len(entries) or claimed_root!=commitment(entries):return self._record('INBOX_COMMITMENT_MISMATCH',{'observed':len(entries),'claimed':claimed_count})
        expected=set(range(start,end+1));present=set(by_seq)
        missing=sorted(expected-present)
        # Authenticated sender payload hash list is needed to bind ack to original payload.
        hashes=s.get('payload_hashes')
        if not isinstance(hashes,list) or len(hashes)!=end-start+1 or any(not isinstance(x,str) or len(x)!=64 for x in hashes):return self._record('INVALID_SENDER_MANIFEST',{})
        for n,r in by_seq.items():
            if r.get('payload_hash')!=hashes[n-start]:return self._record('PAYLOAD_MISMATCH',{'seq':n})
        if not self.ledger.reserve('receiver',w['nonce']):return self._record('REPLAY_WATERMARK',{})
        if missing:return self._record('WATERMARK_COVERAGE_GAP',{'missing':missing,'signed_watermark':end})
        return self._record('COMPLETE_SIGNED_INBOX_FIXTURE',{'covered':len(present),'through':end})
    def _record(self,status,data):
        result={'status':status,**data,'active':self.active,'independent_physical_custody':False,'automatic_learning':False}
        self.ledger.append(result);return result
    def close(self):self.ledger.close()

def keys():
    a=Ed25519PrivateKey.from_private_bytes(bytes(range(1,33)))
    b=Ed25519PrivateKey.from_private_bytes(bytes(range(33,65)))
    return a,b

def fixture(present=(1,2,3),through=3,nonce='wm-1',now=1000):
    sk,rk=keys()
    payloads=[hashof({'seq':i,'message':f'payload-{i}'}) for i in range(1,through+1)]
    s={'domain':'JANE187:sender:v1','start':1,'end':through,'payload_hashes':payloads}
    sender=Signed.issue(sk,s)
    entries=[{'domain':'JANE187:ack:v1','seq':i,'sender_digest':hashof(s),'payload_hash':payloads[i-1]} for i in present]
    receipts=[Signed.issue(rk,e) for e in entries]
    w={'domain':'JANE187:watermark:v1','start':1,'through':through,'sender_digest':hashof(s),
       'count':len(entries),'inbox_commitment':commitment(entries),'issued_at':now,'nonce':nonce}
    watermark=Signed.issue(rk,w)
    return (sk.public_key(),rk.public_key()),sender,watermark,receipts

def demo():
    (sk,rk),s,w,rs=fixture((1,3))
    f=FLAY(sk,rk)
    try:
        gap=f.audit(s,w,rs)
        (sk,rk),s,w,rs=fixture((1,2,3),nonce='wm-2')
        full=f.audit(s,w,rs)
        return {'experiment':'JANE-187','gap':gap,'complete':full,'audit_chain_valid':f.ledger.check(),
                'scope':'signed local synthetic custody fixtures; not proof of physical delivery'}
    finally:f.close()
if __name__=='__main__':print(json.dumps(demo(),indent=2))
