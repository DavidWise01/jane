"""JANE 189 — Fresh challenge-bound effect receipts (fixture trust model)."""
import hashlib, json, sqlite3, secrets
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

def enc(x): return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def sha(x): return hashlib.sha256(x).hexdigest()
def sign(key,body):return key.sign(enc(body)).hex()
def verify(key,body,sig):
    try:key.verify(bytes.fromhex(sig),enc(body));return True
    except (ValueError,TypeError,InvalidSignature):return False

def fixture_keys():
    names=('issuer','executor','observerA','observerB')
    return {n:Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('JANE189-TEST-'+n).encode()).digest()) for n in names}

def packet(key, signer, body):return {'signer':signer,'body':body,'signature':sign(key,body)}

def challenge(key,input_bytes,sequence,issued_ms,deadline_ms,nonce=None):
    if nonce is None:nonce=secrets.token_hex(16)
    if not isinstance(nonce,str) or len(nonce)!=32 or any(c not in '0123456789abcdef' for c in nonce):raise ValueError('128-bit hex challenge required')
    if not isinstance(sequence,int) or isinstance(sequence,bool) or sequence<1 or not isinstance(issued_ms,int) or deadline_ms<=issued_ms:raise ValueError('invalid window')
    return packet(key,'issuer',{'type':'CHALLENGE','seq':sequence,'input_sha256':sha(input_bytes),'nonce':nonce,'issued_ms':issued_ms,'deadline_ms':deadline_ms})

def execution(key,request,output,observed_ms,status='SUCCEEDED'):
    q=request['body']
    return packet(key,'executor',{'type':'EXECUTION','seq':q['seq'],'input_sha256':q['input_sha256'],'nonce':q['nonce'],'output_sha256':sha(output),'observed_ms':observed_ms,'status':status})

def effect(key,signer,request,output,observed_ms,source_id):
    q=request['body']
    return packet(key,signer,{'type':'EFFECT','seq':q['seq'],'nonce':q['nonce'],'output_sha256':sha(output),'observed_ms':observed_ms,'source_id':source_id})

class FLAY:
    def __init__(self,db_path,public,roots):
        self.db=sqlite3.connect(db_path)
        self.db.execute('create table if not exists challenges (nonce text primary key, request_digest text not null, verdict text not null)')
        self.db.execute('create table if not exists audit (id integer primary key, prev text not null, payload text not null, head text not null)')
        self.db.commit();self.public=public;self.roots=roots;self.active='frozen_parent'
    def close(self):self.db.close()
    def _auth(self,claim,who,kind):
        return (isinstance(claim,dict) and claim.get('signer')==who and isinstance(claim.get('body'),dict)
                and claim['body'].get('type')==kind and who in self.public
                and verify(self.public[who],claim['body'],claim.get('signature','')))
    def _record(self,nonce,verdict,summary):
        prior=self.db.execute('select head from audit order by id desc limit 1').fetchone()
        prev=prior[0] if prior else '0'*64
        payload={'nonce':nonce,'verdict':verdict,'summary':summary,'active':'frozen_parent','learning_applied':False}
        head=sha(enc({'prev':prev,'payload':payload}))
        self.db.execute('insert into audit(prev,payload,head) values(?,?,?)',(prev,enc(payload).decode(),head))
        if nonce is not None and self.db.execute('select 1 from challenges where nonce=?',(nonce,)).fetchone() is None:
            self.db.execute('insert into challenges values(?,?,?)',(nonce,summary.get('request_digest',''),verdict))
        self.db.commit();return verdict
    def audit_ok(self):
        prev='0'*64;expected=1
        for ident,p,raw,h in self.db.execute('select id,prev,payload,head from audit order by id'):
            if ident!=expected or p!=prev or h!=sha(enc({'prev':p,'payload':json.loads(raw)})):return False
            expected+=1;prev=h
        return True
    def review(self,input_bytes,request,run,observations,now_ms,quorum=2):
        """Authenticates claims; no claim of actual processing or independent physical custody."""
        if not self._auth(request,'issuer','CHALLENGE'):
            return self._record(None,'BAD_CHALLENGE_SIGNATURE',{})
        q=request['body'];nonce=q.get('nonce')
        if not isinstance(nonce,str) or len(nonce)!=32 or any(c not in '0123456789abcdef' for c in nonce):return self._record(None,'BAD_NONCE',{})
        summary={'seq':q.get('seq'),'request_digest':sha(enc(request))}
        # Every inspected authentic request consumes its nonce, even on invalid run/effect evidence.
        if self.db.execute('select 1 from challenges where nonce=?',(nonce,)).fetchone():return self._record(None,'REPLAY',summary)
        if q.get('input_sha256')!=sha(input_bytes):return self._record(nonce,'INPUT_MISMATCH',summary)
        if type(now_ms)!=int or type(q.get('issued_ms'))!=int or type(q.get('deadline_ms'))!=int or not q['issued_ms']<=now_ms<=q['deadline_ms']:
            return self._record(nonce,'CHALLENGE_EXPIRED_OR_FUTURE',summary)
        if not self._auth(run,'executor','EXECUTION'):
            return self._record(nonce,'BAD_EXECUTION_SIGNATURE',summary)
        r=run['body'];bound=('seq','input_sha256','nonce')
        if any(r.get(k)!=q.get(k) for k in bound):return self._record(nonce,'EXECUTION_NOT_BOUND',summary)
        if type(r.get('observed_ms'))!=int or not q['issued_ms']<=r['observed_ms']<=now_ms or r['observed_ms']>q['deadline_ms']:
            return self._record(nonce,'EXECUTION_TIME_UNSUPPORTED',summary)
        if r.get('status')!='SUCCEEDED':return self._record(nonce,'FAILED_ATTEMPT_PRESERVED',summary)
        if not isinstance(r.get('output_sha256'),str) or len(r['output_sha256'])!=64:return self._record(nonce,'BAD_OUTPUT_HASH',summary)
        if not observations:return self._record(nonce,'SUCCESS_UNCORROBORATED',summary)
        roots=set();seen=set();sourceids=set()
        for obs in observations:
            signer=obs.get('signer') if isinstance(obs,dict) else None
            if signer in seen:return self._record(nonce,'DUPLICATE_OBSERVER',summary)
            seen.add(signer)
            if signer not in self.roots or not self._auth(obs,signer,'EFFECT'):return self._record(nonce,'BAD_EFFECT_SIGNATURE',summary)
            b=obs['body']
            if b.get('seq')!=q['seq'] or b.get('nonce')!=nonce or b.get('output_sha256')!=r['output_sha256']:
                return self._record(nonce,'STAGED_OR_MISMATCHED_EFFECT',summary)
            if type(b.get('observed_ms'))!=int or not r['observed_ms']<=b['observed_ms']<=now_ms or b['observed_ms']>q['deadline_ms']:
                return self._record(nonce,'EFFECT_ORDER_UNSUPPORTED',summary)
            if not isinstance(b.get('source_id'),str) or not b['source_id']:return self._record(nonce,'MISSING_ACQUISITION_SOURCE',summary)
            roots.add(self.roots[signer]);sourceids.add(b['source_id'])
        if len(roots)<quorum or len(sourceids)<quorum:return self._record(nonce,'SHARED_OR_INSUFFICIENT_ANCESTRY',summary)
        return self._record(nonce,'FRESH_EFFECT_FIXTURE_CORROBORATED',summary)

def demo():
    keys=fixture_keys();pub={k:v.public_key() for k,v in keys.items()}
    db=FLAY(':memory:',pub,{'observerA':'rootA','observerB':'rootB'})
    q=challenge(keys['issuer'],b'job',1,100,200,nonce='a'*32)
    run=execution(keys['executor'],q,b'out',120)
    obs=[effect(keys[n],n,q,b'out',130,source) for n,source in [('observerA','instrumentA'),('observerB','instrumentB')]]
    good=db.review(b'job',q,run,obs,140)
    again=db.review(b'job',q,run,obs,140)
    result={'experiment':'JANE-189','status':good,'replay':again,'audit_ok':db.audit_ok(),'fixture_only':True,'active':'frozen_parent','learning_applied':False}
    db.close();return result
if __name__=='__main__':print(json.dumps(demo(),indent=2))