"""JANE 182 — explicit prefix-Merkle consistency proof (bounded O(n log n)).

This deliberately uses one inclusion path per prior leaf, not the compact RFC 6962
consistency proof. The old root is recomputed from the supplied prefix leaves,
and each of those *same* leaves is independently proven at its exact index in
new signed checkpoint. Neither signature alone nor a previous_root link suffices.
"""
import hashlib, json, sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

def enc(x): return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def h(x): return hashlib.sha256(x).hexdigest()
def leaf(data): return h(b'\x00'+enc(data))
def join(a,b): return h(b'\x01'+bytes.fromhex(a)+bytes.fromhex(b))
def root(leaves):
    if not leaves:return h(b'\x02'+(0).to_bytes(8,'big')+bytes.fromhex(h(b'')))
    layer=list(leaves)
    while len(layer)>1:
        layer=[join(layer[i],layer[i+1]) if i+1<len(layer) else layer[i] for i in range(0,len(layer),2)]
    return h(b'\x02'+len(leaves).to_bytes(8,'big')+bytes.fromhex(layer[0]))
def path(leaves,index):
    if not 0<=index<len(leaves):raise ValueError('index')
    layer=list(leaves);out=[];i=index
    while len(layer)>1:
        if i%2:out.append(['L',layer[i-1]])
        elif i+1<len(layer):out.append(['R',layer[i+1]])
        else:out.append(['N',None])
        layer=[join(layer[j],layer[j+1]) if j+1<len(layer) else layer[j] for j in range(0,len(layer),2)]
        i//=2
    return out
def verify_path(value,index,total,steps,expected):
    if total<1 or not 0<=index<total:return False
    current=value;i=index;n=total;pos=0
    while n>1:
        if pos>=len(steps) or not isinstance(steps[pos],list) or len(steps[pos])!=2:return False
        side,hash_other=steps[pos];pos+=1
        if i%2:
            if side!='L' or not is_hash(hash_other):return False
            current=join(hash_other,current)
        elif i+1<n:
            if side!='R' or not is_hash(hash_other):return False
            current=join(current,hash_other)
        elif side!='N' or hash_other is not None:return False
        i//=2;n=(n+1)//2
    return pos==len(steps) and h(b'\x02'+total.to_bytes(8,'big')+bytes.fromhex(current))==expected
def is_hash(x):return isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x)
@dataclass(frozen=True)
class Key:
    identity:str
    administrator:str
    private:object
    @property
    def public(self):return self.private.public_key()
def sign(key,body):return {'body':body,'signer':key.identity,'signature':key.private.sign(enc(body)).hex()}
def check(receipt,keys):
    try:
        key=keys[receipt['signer']]
        key.public.verify(bytes.fromhex(receipt['signature']),enc(receipt['body']))
        return True
    except (KeyError,ValueError,InvalidSignature,TypeError,AttributeError):return False
def fixture_key(name,admin):return Key(name,admin,Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('jane182:'+name).encode()).digest()))
def checkpoint(leaves,keys,epoch,nonce):
    body={'kind':'jane182.checkpoint','size':len(leaves),'root':root(leaves),'epoch':epoch,'nonce':nonce}
    return [sign(k,body) for k in keys]
def make_proof(old_leaves,new_leaves):
    if len(old_leaves)>len(new_leaves):raise ValueError('old larger than new')
    return {'kind':'jane182.explicit-prefix-v1','old_size':len(old_leaves),'new_size':len(new_leaves),
            'prefix':list(old_leaves), 'paths':[path(new_leaves,i) for i in range(len(old_leaves))]}
class Audit:
    def __init__(self,keys,db=':memory:',quorum=3,max_old=64,max_new=128):
        self.keys={k.identity:k for k in keys};self.db=sqlite3.connect(db);self.quorum=quorum
        self.max_old=max_old;self.max_new=max_new
        self.db.execute('CREATE TABLE IF NOT EXISTS used (signer TEXT, nonce TEXT, PRIMARY KEY(signer,nonce))')
        self.db.execute('CREATE TABLE IF NOT EXISTS heads (epoch INTEGER PRIMARY KEY, size INTEGER, root TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY AUTOINCREMENT, previous TEXT, entry TEXT, head TEXT)')
        self.db.commit()
    def close(self):self.db.close()
    def log(self,reason,details):
        prev=self.db.execute('SELECT head FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
        previous=prev[0] if prev else '0'*64
        entry=json.dumps({'reason':reason,'details':details},sort_keys=True)
        head=h((previous+entry).encode())
        self.db.execute('INSERT INTO audit(previous,entry,head) VALUES (?,?,?)',(previous,entry,head));self.db.commit()
    def validate_checkpoint(self,receipts):
        if not receipts:return 'INSUFFICIENT_ATTESTATION',None,[]
        body=receipts[0].get('body')
        if not isinstance(body,dict) or body.get('kind')!='jane182.checkpoint':return 'BAD_CHECKPOINT',None,[]
        if type(body.get('size')) is not int or not 0<=body['size']<=self.max_new or not is_hash(body.get('root')) or type(body.get('epoch')) is not int or not isinstance(body.get('nonce'),str):return 'BAD_CHECKPOINT',None,[]
        seen=set();admins=set();signers=[]
        for rec in receipts:
            if rec.get('body')!=body:return 'CONFLICTING_CHECKPOINTS',None,[]
            who=rec.get('signer')
            if who in seen:return 'DUPLICATE_SIGNER',None,[]
            if not check(rec,self.keys):return 'BAD_SIGNATURE',None,[]
            seen.add(who);admins.add(self.keys[who].administrator);signers.append(who)
        if len(admins)<self.quorum:return 'INSUFFICIENT_DISTINCT_ADMINISTRATORS',None,[]
        for s in signers:
            if self.db.execute('SELECT 1 FROM used WHERE signer=? AND nonce=?',(s,body['nonce'])).fetchone():return 'REPLAY',None,[]
        return 'VALID',body,signers
    def reconcile(self,old_receipts,new_receipts,proof):
        state,old,oldsign=self.validate_checkpoint(old_receipts)
        if state!='VALID':self.log(state,{'checkpoint':'old'});return state
        state,new,newsign=self.validate_checkpoint(new_receipts)
        if state!='VALID':self.log(state,{'checkpoint':'new'});return state
        if old['nonce']==new['nonce'] or new['epoch']<=old['epoch'] or new['size']<old['size']:
            status='ROLLBACK_OR_REPLAY'
        elif old['size']>self.max_old or not isinstance(proof,dict) or proof.get('kind')!='jane182.explicit-prefix-v1' or proof.get('old_size')!=old['size'] or proof.get('new_size')!=new['size']:
            status='INVALID_PROOF_DOMAIN'
        elif not isinstance(proof.get('prefix'),list) or not isinstance(proof.get('paths'),list) or len(proof['prefix'])!=old['size'] or len(proof['paths'])!=old['size']:
            status='INCOMPLETE_PROOF'
        elif not all(is_hash(v) for v in proof['prefix']) or root(proof['prefix'])!=old['root']:
            status='OLD_ROOT_MISMATCH'
        elif not all(verify_path(v,i,new['size'],p,new['root']) for i,(v,p) in enumerate(zip(proof['prefix'],proof['paths']))):
            status='PREFIX_NOT_PRESERVED'
        else:
            previous=self.db.execute('SELECT size,root FROM heads WHERE epoch=?',(new['epoch'],)).fetchone()
            if previous and previous!=(new['size'],new['root']):status='CHECKPOINT_FORK'
            else:status='CONSISTENT_APPEND_ONLY_FIXTURE'
        if status=='CONSISTENT_APPEND_ONLY_FIXTURE':
            for s in oldsign:self.db.execute('INSERT INTO used VALUES (?,?)',(s,old['nonce']))
            for s in newsign:self.db.execute('INSERT INTO used VALUES (?,?)',(s,new['nonce']))
            self.db.execute('INSERT OR IGNORE INTO heads VALUES (?,?,?)',(old['epoch'],old['size'],old['root']))
            self.db.execute('INSERT OR IGNORE INTO heads VALUES (?,?,?)',(new['epoch'],new['size'],new['root']))
            self.db.commit()
        self.log(status,{'old_size':old['size'],'new_size':new['size'],'old_root':old['root'],'new_root':new['root']})
        return status
    def audit_chain(self):
        prev='0'*64
        for previous,entry,head in self.db.execute('SELECT previous,entry,head FROM audit ORDER BY seq'):
            if previous!=prev or head!=h((prev+entry).encode()):return 'TAMPERED'
            prev=head
        return 'VALID_LOCAL_CHAIN'
def demo():
    keys=[fixture_key('w'+str(i),'admin'+str(i)) for i in range(3)]
    old=[leaf({'sequence':i,'value':i*i}) for i in range(1,7)]
    new=old+[leaf({'sequence':i,'value':i*i}) for i in range(7,10)]
    auditor=Audit(keys)
    result=auditor.reconcile(checkpoint(old,keys,6,'old'),checkpoint(new,keys,9,'new'),make_proof(old,new))
    result_packet={'experiment':'JANE-182','status':result,'old_size':6,'new_size':9,'old_root':root(old),'new_root':root(new),'audit':auditor.audit_chain(),'independence_verified':False,'active_parent_changed':False,'proof_type':'explicit prefix inclusion (O(n log n))','scope':'local synthetic witness fixtures'}
    auditor.close();return result_packet
if __name__=='__main__':print(json.dumps(demo(),indent=2))