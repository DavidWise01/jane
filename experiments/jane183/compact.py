"""JANE 183: compact RFC6962-style prefix consistency over size-bound signed roots.

Proof nodes are raw Merkle subtree hashes; signed roots are size-bound wrappers.
The proof authenticates unchanged prefix leaves, not external time or independence.
"""
import hashlib, json
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

def enc(x): return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def h(b): return hashlib.sha256(b).digest()
def leaf(v): return h(b'\x00'+enc(v))
def node(a,b): return h(b'\x01'+a+b)
def split(n): return 1 << ((n-1).bit_length()-1)
def internal(xs):
    if not xs: return h(b'')
    if len(xs)==1:return xs[0]
    k=split(len(xs));return node(internal(xs[:k]),internal(xs[k:]))
def commit(xs):return h(b'\x02'+len(xs).to_bytes(8,'big')+internal(xs)).hex()
def hash_ok(v):return type(v) is str and len(v)==64 and all(c in '0123456789abcdef' for c in v)
def subproof(xs,m,complete):
    n=len(xs)
    if m==n:return [] if complete else [internal(xs)]
    k=split(n)
    if m<=k:return subproof(xs[:k],m,complete)+[internal(xs[k:])]
    return subproof(xs[k:],m-k,False)+[internal(xs[:k])]
def proof(xs,m):
    if type(m) is not int or not 1<=m<=len(xs):raise ValueError('invalid prefix size')
    return dict(kind='jane183.consistency.v1',old_size=m,new_size=len(xs),nodes=[x.hex() for x in subproof(xs,m,True)])
def verify(p,old_root,new_root,max_size=1024):
    if not isinstance(p,dict) or p.get('kind')!='jane183.consistency.v1':return False
    m=p.get('old_size');n=p.get('new_size');nodes=p.get('nodes')
    if type(m) is not int or type(n) is not int or not 1<=m<=n<=max_size or not isinstance(nodes,list) or len(nodes)>2*n.bit_length() or not all(hash_ok(x) for x in nodes) or not hash_ok(old_root) or not hash_ok(new_root):return False
    source=[bytes.fromhex(x) for x in nodes];pos=0
    # Reconstruct both raw tree roots using old signed root as a check only at the end.
    # At complete=true, old subtree root is not in proof; derive via a frontier variable
    # extracted from old root is impossible due to its size-bound hash wrapper.
    # Therefore compact proofs carry the raw old root as a separately verified commitment opening.
    old_raw=p.get('old_internal')
    if not hash_ok(old_raw) or h(b'\x02'+m.to_bytes(8,'big')+bytes.fromhex(old_raw)).hex()!=old_root:return False
    def consume():
        nonlocal pos
        if pos>=len(source):raise ValueError('short proof')
        value=source[pos];pos+=1;return value
    def walk(m,n,complete):
        if m==n:
            if complete:return bytes.fromhex(old_raw),bytes.fromhex(old_raw)
            v=consume();return v,v
        k=split(n)
        if m<=k:
            o,nleft=walk(m,k,complete)
            right=consume()
            return o,node(nleft,right)
        o,nright=walk(m-k,n-k,False)
        left=consume()
        return node(left,o),node(left,nright)
    try:oa,na=walk(m,n,True)
    except (ValueError,RecursionError):return False
    return pos==len(source) and oa.hex()==old_raw and h(b'\x02'+n.to_bytes(8,'big')+na).hex()==new_root

def make_proof(xs,m):
    p=proof(xs,m);p['old_internal']=internal(xs[:m]).hex();return p

@dataclass(frozen=True)
class Signer:
    name:str
    administrator:str
    private:object
    @property
    def public(self):return self.private.public_key()
def signer(name,admin):return Signer(name,admin,Ed25519PrivateKey.from_private_bytes(h(('JANE183:'+name).encode())))
def signed_checkpoint(xs,signers,epoch,nonce):
    body=dict(schema='jane183.checkpoint.v1',size=len(xs),root=commit(xs),epoch=epoch,nonce=nonce)
    return [{'body':body,'signer':s.name,'signature':s.private.sign(enc(body)).hex()} for s in signers]
class FLAY:
    def __init__(self,signers,quorum=3):
        self.keys={s.name:s for s in signers};self.quorum=quorum;self.used=set();self.events=[];self.heads={};self.active='frozen_parent'
    def append(self,status,detail):
        event={'seq':len(self.events),'status':status,'detail':detail,'previous':self.events[-1]['digest'] if self.events else '0'*64}
        event['digest']=h(enc(event)).hex();self.events.append(event)
    def audit(self):
        prior='0'*64
        for i,e in enumerate(self.events):
            if e.get('seq')!=i or e.get('previous')!=prior or e.get('digest')!=h(enc({k:v for k,v in e.items() if k!='digest'})).hex():return 'TAMPERED'
            prior=e['digest']
        return 'VALID_LOCAL_CHAIN'
    def checkpoint(self,receipts):
        if not isinstance(receipts,list) or not receipts:return ('INSUFFICIENT_CUSTODY',None,[])
        b=receipts[0].get('body',{})
        if not isinstance(b,dict) or b.get('schema')!='jane183.checkpoint.v1' or type(b.get('size')) is not int or not 1<=b['size']<=1024 or not hash_ok(b.get('root')) or type(b.get('epoch')) is not int or not isinstance(b.get('nonce'),str):return ('BAD_CHECKPOINT',None,[])
        seen=set();admins=set()
        for rec in receipts:
            if rec.get('body')!=b:return ('CONFLICTING_CLAIMS',None,[])
            who=rec.get('signer');key=self.keys.get(who)
            if who in seen:return ('DUPLICATE_SIGNER',None,[])
            if key is None:return ('UNKNOWN_SIGNER',None,[])
            try:key.public.verify(bytes.fromhex(rec['signature']),enc(b))
            except (InvalidSignature,ValueError,KeyError,TypeError):return ('BAD_SIGNATURE',None,[])
            seen.add(who);admins.add(key.administrator)
            if (who,b['nonce']) in self.used:return ('REPLAY',None,[])
        if len(admins)<self.quorum:return ('SHARED_OR_INSUFFICIENT_CUSTODY',None,[])
        return 'VALID',b,seen
    def reconcile(self,old_receipts,new_receipts,p):
        status,old,oldsign=self.checkpoint(old_receipts)
        if status!='VALID':self.append(status,'old');return status
        status,new,newsign=self.checkpoint(new_receipts)
        if status!='VALID':self.append(status,'new');return status
        if new['epoch']<=old['epoch'] or new['size']<old['size'] or new['nonce']==old['nonce']:status='ROLLBACK_OR_REPLAY'
        elif not isinstance(p,dict) or p.get('old_size')!=old['size'] or p.get('new_size')!=new['size'] or not verify(p,old['root'],new['root']):status='INCONSISTENT_PREFIX'
        elif new['epoch'] in self.heads and self.heads[new['epoch']]!=(new['size'],new['root']):status='FORK'
        else:status='CONSISTENT_COMPACT_FIXTURE'
        if status=='CONSISTENT_COMPACT_FIXTURE':
            self.used.update((who,old['nonce']) for who in oldsign)
            self.used.update((who,new['nonce']) for who in newsign)
            self.heads[old['epoch']]=(old['size'],old['root'])
            self.heads[new['epoch']]=(new['size'],new['root'])
        self.append(status,dict(old=old['root'],new=new['root'],old_size=old['size'],new_size=new['size']))
        return status

def demo():
    xs=[leaf({'sequence':i,'value':i*i}) for i in range(1,10)]
    keys=[signer('root'+str(i),'administrator'+str(i)) for i in range(3)]
    f=FLAY(keys)
    p=make_proof(xs,6)
    result=f.reconcile(signed_checkpoint(xs[:6],keys,6,'six'),signed_checkpoint(xs,keys,9,'nine'),p)
    return dict(experiment='JANE-183',status=result,old_size=6,new_size=9,proof_hashes=len(p['nodes'])+1,
                old_root=commit(xs[:6]),new_root=commit(xs),audit=f.audit(),independent_custodians_verified=False,
                active_parent_changed=False,scope='RFC6962-style compact consistency; fixture custody only')
if __name__=='__main__':print(json.dumps(demo(),indent=2))