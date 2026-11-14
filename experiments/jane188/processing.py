"""JANE 188: receipt != execution != corroborated effect.

All signatures and observers are local fixtures. No physical execution is proved.
"""
import hashlib, json, sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

def canonical(o): return json.dumps(o,sort_keys=True,separators=(',',':')).encode()
def H(blob): return hashlib.sha256(blob).hexdigest()
def body_hash(obj): return H(canonical(obj))
def sign(key, body): return key.sign(canonical(body)).hex()
def verify(pub, body, sig):
    try:
        pub.verify(bytes.fromhex(sig),canonical(body));return True
    except (InvalidSignature,ValueError,TypeError):return False

def keys():
    return {name:Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('jane188-test-'+name).encode()).digest()) for name in ('sender','receiver','executor','observerA','observerB')}

@dataclass(frozen=True)
class Trust:
    public:dict
    roots:dict
    @classmethod
    def fixture(cls, priv):
        return cls({n:k.public_key() for n,k in priv.items()}, {'observerA':'fixture_root_A','observerB':'fixture_root_B'})

def receipt(key, seq, data):
    b={'kind':'RECEIVED','seq':seq,'input_sha256':H(data)}
    return {'body':b,'signature':sign(key,b),'signer':'receiver'}

def execution(key, seq, input_sha, output_sha, status='SUCCEEDED',attempt=1):
    b={'kind':'EXECUTION','seq':seq,'input_sha256':input_sha,'output_sha256':output_sha,'status':status,'attempt':attempt}
    return {'body':b,'signature':sign(key,b),'signer':'executor'}

def observation(key, name, seq, output_sha, status='OBSERVED', nonce='n'):
    b={'kind':'EFFECT','seq':seq,'output_sha256':output_sha,'status':status,'nonce':nonce}
    return {'body':b,'signature':sign(key,b),'signer':name}

class Auditor:
    def __init__(self, path=':memory:', trust=None):
        if trust is None:raise ValueError('trust required')
        self.trust=trust;self.db=sqlite3.connect(path)
        self.db.execute('create table if not exists decisions (id text primary key, verdict text not null, digest text not null)')
        self.db.execute('create table if not exists audit (idx integer primary key, predecessor text not null, payload text not null, head text not null)')
        self.db.commit()
    def close(self):self.db.close()
    def _write(self, identity, verdict, summary):
        payload={'identity':identity,'verdict':verdict,'summary':summary}
        prior=self.db.execute('select head from audit order by idx desc limit 1').fetchone()
        prev=prior[0] if prior else '0'*64
        head=body_hash({'previous':prev,'payload':payload})
        self.db.execute('insert into audit(predecessor,payload,head) values(?,?,?)',(prev,canonical(payload).decode(),head))
        if identity is not None:
            self.db.execute('insert into decisions values(?,?,?)',(identity,verdict,body_hash(summary)))
        self.db.commit()
        return verdict
    def ledger_ok(self):
        prev='0'*64
        for idx,p,raw,h in self.db.execute('select idx,predecessor,payload,head from audit order by idx'):
            if p!=prev or h!=body_hash({'previous':p,'payload':json.loads(raw)}):return False
            prev=h
        return True
    def _auth(self,item,kind,who):
        if not isinstance(item,dict) or item.get('signer')!=who:return False
        b=item.get('body')
        return isinstance(b,dict) and b.get('kind')==kind and who in self.trust.public and verify(self.trust.public[who],b,item.get('signature',''))
    def review(self, inbound, receipt_item, exec_item=None, effects=(), min_roots=2):
        """Returns epistemic classification. Does not execute messages or activate learning."""
        seq=inbound['seq'];raw=inbound['data'];sha=H(raw)
        identity=body_hash({'seq':seq,'input_sha256':sha,'receipt':receipt_item,'execution':exec_item,'effects':list(effects)})
        if self.db.execute('select 1 from decisions where id=?',(identity,)).fetchone():
            return self._write(None,'REPLAY',{'seq':seq})
        summary={'seq':seq,'input_sha256':sha,'effect_count':len(effects),'active':'frozen_parent','learning_applied':False}
        if not self._auth(receipt_item,'RECEIVED','receiver') or receipt_item['body'].get('seq')!=seq or receipt_item['body'].get('input_sha256')!=sha:
            return self._write(identity,'UNAUTHENTIC_RECEIPT',summary)
        if exec_item is None:return self._write(identity,'RECEIPT_ONLY',summary)
        if not self._auth(exec_item,'EXECUTION','executor') or exec_item['body'].get('seq')!=seq or exec_item['body'].get('input_sha256')!=sha:
            return self._write(identity,'UNAUTHENTIC_EXECUTION_CLAIM',summary)
        claim=exec_item['body'];summary['claimed_status']=claim['status'];summary['output_sha256']=claim['output_sha256']
        if claim['status']!='SUCCEEDED':return self._write(identity,'FAILED_ATTEMPT_PRESERVED',summary)
        if not isinstance(claim['output_sha256'],str) or len(claim['output_sha256'])!=64:
            return self._write(identity,'MALFORMED_OUTPUT_COMMITMENT',summary)
        if not effects:return self._write(identity,'SUCCESS_CLAIM_UNCORROBORATED',summary)
        roots=set();signers=set();nonces=set();conflict=False;invalid=False
        for item in effects:
            who=item.get('signer') if isinstance(item,dict) else None
            if who not in self.trust.roots or not self._auth(item,'EFFECT',who):invalid=True;continue
            b=item['body']
            if b.get('seq')!=seq or b.get('status')!='OBSERVED':invalid=True;continue
            if who in signers or (who,b.get('nonce')) in nonces:invalid=True;continue
            signers.add(who);nonces.add((who,b.get('nonce')))
            if b.get('output_sha256')!=claim['output_sha256']:conflict=True
            roots.add(self.trust.roots[who])
        summary['declared_roots']=len(roots)
        if invalid:return self._write(identity,'INVALID_EFFECT_EVIDENCE',summary)
        if conflict:return self._write(identity,'EFFECT_CONFLICT',summary)
        if len(roots)<min_roots:return self._write(identity,'INSUFFICIENT_EFFECT_ANCESTRY',summary)
        return self._write(identity,'CORROBORATED_FIXTURE_EFFECT',summary)

def demo():
    ks=keys();t=Trust.fixture(ks);msg={'seq':1,'data':b'input-v1'}
    r=receipt(ks['receiver'],1,msg['data']);out=H(b'output-v1')
    ex=execution(ks['executor'],1,H(msg['data']),out)
    observations=[observation(ks[n],n,1,out,nonce=n) for n in ('observerA','observerB')]
    a=Auditor(trust=t)
    results={'receipt_only':a.review(msg,r), 'unsupported_success':a.review(msg,r,ex), 'independent_fixture_effects':a.review(msg,r,ex,observations), 'replay':a.review(msg,r,ex,observations),'ledger_ok':a.ledger_ok(),'tests_scope':'local signed fixtures; no real world execution or independent custody','active':'frozen_parent'}
    a.close();return results
if __name__=='__main__':print(json.dumps(demo(),indent=2))