"""JANE 181: evidence commitments and append-only Merkle witness receipts.

Fixtures are synthetic. A valid inclusion proof gives a position in a signed
log snapshot, NOT independently trusted wall-clock time or physical independence.
"""
import hashlib, json, sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':')).encode()
def h(b): return hashlib.sha256(b).digest()
def leaf(b): return h(b'\x00'+b)
def branch(a,b): return h(b'\x01'+a+b)
def hexh(b): return b.hex()
def commit(blob): return hexh(h(blob))
def merkle_root(leaves):
    if not leaves:return h(b'\x02'+(0).to_bytes(8,'big')+h(b''))
    level=[leaf(b) for b in leaves]
    while len(level)>1:
        level=[branch(level[i],level[i+1]) if i+1<len(level) else level[i] for i in range(0,len(level),2)]
    return h(b'\x02'+len(leaves).to_bytes(8,'big')+level[0])
def proof(leaves,index):
    if not 0<=index<len(leaves):raise ValueError('index outside log')
    level=[leaf(b) for b in leaves];j=index;path=[]
    while len(level)>1:
        sibling=j^1
        if sibling<len(level):path.append({'side':'left' if sibling<j else 'right','hash':hexh(level[sibling])})
        else:path.append({'side':'promoted'})
        level=[branch(level[i],level[i+1]) if i+1<len(level) else level[i] for i in range(0,len(level),2)]
        j//=2
    return path
def verify_inclusion(blob,index,size,root,path):
    if type(size)!=int or type(index)!=int or not 0<=index<size:return False
    try:
        node=leaf(blob);j=index;n=size;k=0
        while n>1:
            side=path[k];k+=1
            if j%2==1:
                if side['side']!='left':return False
                node=branch(bytes.fromhex(side['hash']),node)
            elif j+1<n:
                if side['side']!='right':return False
                node=branch(node,bytes.fromhex(side['hash']))
            else:
                if side['side']!='promoted':return False
            j//=2;n=(n+1)//2
        return k==len(path) and h(b'\x02'+size.to_bytes(8,'big')+node).hex()==root
    except (IndexError,KeyError,ValueError,TypeError):return False

def signing_bytes(checkpoint):return canon({k:checkpoint[k] for k in ('log_id','size','root','observed_at','prev_root','nonce')})
@dataclass
class Operator:
    name:str
    administration:str
    key:Ed25519PrivateKey
    @classmethod
    def fixture(cls,name,admin,seed):return cls(name,admin,Ed25519PrivateKey.from_private_bytes(h(seed.encode())))
    def public(self):return self.key.public_key()
    def receipt(self,cp):return {'operator':self.name,'signature':self.key.sign(signing_bytes(cp)).hex()}

class Audit:
    def __init__(self,db=':memory:',operators=None,required=2):
        self.db=sqlite3.connect(db);self.db.execute('CREATE TABLE IF NOT EXISTS heads(log_id TEXT PRIMARY KEY,size INTEGER,root TEXT,observed_at INTEGER)')
        self.db.execute('CREATE TABLE IF NOT EXISTS nonces(operator TEXT,nonce TEXT,PRIMARY KEY(operator,nonce))')
        self.db.execute('CREATE TABLE IF NOT EXISTS evidence(seq INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT,payload TEXT,prior TEXT,hash TEXT)')
        self.db.commit();self.operators=operators or {};self.required=required
    def close(self):self.db.close()
    def record(self,kind,value):
        prev=self.db.execute('SELECT hash FROM evidence ORDER BY seq DESC LIMIT 1').fetchone()
        prior=prev[0] if prev else '0'*64
        payload=canon(value).decode();head=commit(canon({'kind':kind,'payload':payload,'prior':prior}))
        self.db.execute('INSERT INTO evidence(kind,payload,prior,hash) VALUES(?,?,?,?)',(kind,payload,prior,head));self.db.commit()
        return head
    def ledger(self):
        prev='0'*64
        for kind,payload,prior,hashval in self.db.execute('SELECT kind,payload,prior,hash FROM evidence ORDER BY seq'):
            if prior!=prev or commit(canon({'kind':kind,'payload':payload,'prior':prior}))!=hashval:return 'TAMPERED'
            prev=hashval
        return 'VALID_LOCAL_CHAIN'
    def check(self,cp,receipts,entries,index,claimed_created_at,minimum_observed=None):
        """entries: complete local prefix through checkpoint. No network or external time claim."""
        def fail(reason):self.record('REJECT',{'status':reason,'checkpoint':cp});return {'status':reason,'first_observation_proven':False}
        try:
            if not isinstance(cp['size'],int) or cp['size']<1 or cp['size']!=len(entries) or cp['size']>4096:return fail('INCOMPLETE_PREFIX')
            if cp['root']!=hexh(merkle_root(entries)):return fail('LOG_ROOT_MISMATCH')
            if not isinstance(cp['observed_at'],int) or not isinstance(claimed_created_at,int):return fail('INVALID_TIME')
            if claimed_created_at>cp['observed_at']:return fail('CLAIM_AFTER_OBSERVATION')
            if minimum_observed is not None and cp['observed_at']<minimum_observed:return fail('BACKDATED_CLAIM')
            if not isinstance(cp['nonce'],str) or not cp['nonce']:return fail('BAD_NONCE')
            old=self.db.execute('SELECT size,root,observed_at FROM heads WHERE log_id=?',(cp['log_id'],)).fetchone()
            if old:
                if cp['size']<old[0]:return fail('ROLLBACK')
                if cp['size']==old[0] and cp['root']!=old[1]:return fail('EQUIVOCATION')
                if cp['size']==old[0] and cp['root']==old[1]:return fail('REPLAY_CHECKPOINT')
                if cp['observed_at']<old[2]:return fail('OBSERVATION_ORDER_INVALID')
                if cp['prev_root']!=old[1]:return fail('GROWTH_LINK_MISMATCH')
            elif cp['prev_root']!='0'*64:return fail('UNKNOWN_PREDECESSOR')
            if not 0<=index<len(entries):return fail('OMITTED_INCLUSION')
            path=proof(entries,index)
            if not verify_inclusion(entries[index],index,cp['size'],cp['root'],path):return fail('INVALID_INCLUSION')
            seen=set();admins=set();acceptable=[]
            for r in receipts:
                name=r.get('operator');op=self.operators.get(name)
                if not op or name in seen:return fail('UNKNOWN_OR_DUPLICATE_OPERATOR')
                seen.add(name)
                try:op.public().verify(bytes.fromhex(r['signature']),signing_bytes(cp))
                except (InvalidSignature,ValueError,KeyError):return fail('BAD_SIGNATURE')
                if op.administration in admins:return fail('SHARED_ADMINISTRATION')
                admins.add(op.administration)
                if self.db.execute('SELECT 1 FROM nonces WHERE operator=? AND nonce=?',(name,cp['nonce'])).fetchone():return fail('REPLAY_NONCE')
                acceptable.append(name)
            if len(admins)<self.required:return fail('INSUFFICIENT_FIXTURE_ROOTS')
            # Writes take place only after the complete proof and the quorum pass.
            for name in acceptable:self.db.execute('INSERT INTO nonces VALUES(?,?)',(name,cp['nonce']))
            self.db.execute('INSERT OR REPLACE INTO heads VALUES(?,?,?,?)',(cp['log_id'],cp['size'],cp['root'],cp['observed_at']))
            self.db.commit()
            head=self.record('ACCEPT',{'log_id':cp['log_id'],'root':cp['root'],'size':cp['size'],'claimed_created_at':claimed_created_at,'observation':cp['observed_at'],'operators':acceptable,'index':index})
            return {'status':'ANCHORED_INCLUSION_FIXTURE','first_observation_proven':False,'historical_bound_fixture':cp['observed_at'],'index':index,'evidence_head':head,'log_head':cp['root']}
        except (KeyError,TypeError,ValueError):return fail('INVALID_CHECKPOINT')

def fixture():
    ops={name:Operator.fixture(name,admin,seed) for name,admin,seed in [('A','admin_A','seed_A'),('B','admin_B','seed_B'),('C','admin_C','seed_C')]}
    entries=[canon({'decision':i,'payload':'capture-'+str(i)}) for i in range(6)]
    cp={'log_id':'scheduler-1','size':6,'root':hexh(merkle_root(entries)),'observed_at':1000,'prev_root':'0'*64,'nonce':'n-0001'}
    return ops,entries,cp,[ops['A'].receipt(cp),ops['B'].receipt(cp),ops['C'].receipt(cp)]

def demo():
    ops,entries,cp,receipts=fixture();a=Audit(operators=ops,required=3)
    ok=a.check(cp,receipts,entries,2,claimed_created_at=700,minimum_observed=900)
    replay=a.check(cp,receipts,entries,2,claimed_created_at=700)
    bad=dict(cp);bad['nonce']='n-0002';bad['root']='f'*64
    fork=a.check(bad,[ops['A'].receipt(bad),ops['B'].receipt(bad),ops['C'].receipt(bad)],entries,2,700)
    out={'experiment':'JANE-181','tests_scope':'local synthetic fixtures','accepted':ok,'replay':replay['status'],'fork':fork['status'],'ledger':a.ledger(),'learning_applied':False,'independent_operator_verified':False}
    a.close();return out
if __name__=='__main__':print(json.dumps(demo(),indent=2))
