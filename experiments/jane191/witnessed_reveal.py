"""JANE 191: signed commit/witness/reveal fixture; does NOT prove secrecy or physical time."""
import hashlib, json, secrets, sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature


def canonical(x): return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
def sha(x): return hashlib.sha256(x if isinstance(x, bytes) else canonical(x)).hexdigest()
def signed(sk, body): return {'body': body, 'signature': sk.sign(canonical(body)).hex()}
def verify(pk, receipt):
    try:
        pk.verify(bytes.fromhex(receipt['signature']), canonical(receipt['body']))
        return True
    except (InvalidSignature, ValueError, KeyError, TypeError, AttributeError): return False

def deterministic_key(name): return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('JANE191-TEST-'+name).encode()).digest())

def commitment(task_hash, seed):
    if not isinstance(seed, str) or len(seed)!=64 or any(c not in '0123456789abcdef' for c in seed): raise ValueError('256-bit seed expected')
    return sha({'domain':'jane191.commit.v1','task':task_hash,'seed':seed})

@dataclass(frozen=True)
class Trust:
    principal: dict
    witnesses: dict  # witness_id -> (public key, declared admin, declared origin)
    required: int = 2

class Auditor:
    def __init__(self, db, trust):
        self.db=sqlite3.connect(db)
        self.trust=trust
        self.db.execute('CREATE TABLE IF NOT EXISTS reveals(task TEXT, commitment TEXT, PRIMARY KEY(task,commitment))')
        self.db.execute('CREATE TABLE IF NOT EXISTS log(seq INTEGER PRIMARY KEY, prev TEXT NOT NULL, event TEXT NOT NULL, head TEXT NOT NULL)')
        self.db.commit()
    def close(self):self.db.close()
    def audit_log(self):
        prev='0'*64
        for ix,prior,event,head in self.db.execute('SELECT seq,prev,event,head FROM log ORDER BY seq'):
            if prior!=prev or head!=sha({'index':ix,'prev':prior,'event':json.loads(event)}):return False
            prev=head
        return True
    def _record(self,kind,**details):
        row=self.db.execute('SELECT seq,head FROM log ORDER BY seq DESC LIMIT 1').fetchone()
        index=0 if row is None else row[0]+1
        prior='0'*64 if row is None else row[1]
        event={'kind':kind,'details':details}
        head=sha({'index':index,'prev':prior,'event':event})
        self.db.execute('INSERT INTO log VALUES(?,?,?,?)',(index,prior,canonical(event).decode(),head))
        self.db.commit()
    def evaluate(self, freeze, manifest, witnesses, reveal, now):
        """Return a cautious status; all times are SIGNED FIXTURE CLAIMS, not trusted time."""
        def finish(status, **details):
            self._record(status,**details)
            return {'status':status, 'details':details, 'activation':False,'scope':'SIGNED_LOCAL_FIXTURE_ONLY'}
        if not verify(self.trust.principal['task'],freeze):return finish('BAD_TASK_SIGNATURE')
        task=freeze['body']
        if task.get('type')!='freeze' or not isinstance(task.get('task_hash'),str) or len(task['task_hash'])!=64:
            return finish('BAD_TASK_FORMAT')
        if not verify(self.trust.principal['commit'],manifest):return finish('BAD_COMMIT_SIGNATURE')
        cm=manifest['body']
        if cm.get('type')!='commit' or cm.get('task_hash')!=task['task_hash'] or not isinstance(cm.get('seed_commitment'),str) or len(cm['seed_commitment'])!=64:
            return finish('TASK_COMMIT_MISMATCH')
        if not (isinstance(task.get('tick'),int) and isinstance(cm.get('tick'),int) and task['tick']<cm['tick']):return finish('ORDER_INVALID')
        groups=set(); valid=0; conflicts=[]
        for w in witnesses:
            if not isinstance(w,dict) or 'body' not in w:return finish('INVALID_WITNESS')
            body=w['body']; identity=body.get('witness')
            entry=self.trust.witnesses.get(identity)
            if entry is None or not verify(entry[0],w):return finish('BAD_WITNESS_SIGNATURE')
            # Both admin and upstream must be independently declared, and no duplicate signer.
            if (body.get('type')!='witness' or body.get('task_hash')!=task['task_hash'] or
                body.get('seed_commitment')!=cm['seed_commitment'] or body.get('commit_tick')!=cm['tick']):return finish('WITNESS_COMMIT_CONFLICT')
            if identity in [z[0] for z in conflicts]:return finish('DUPLICATE_WITNESS')
            conflicts.append((identity,entry[1],entry[2]))
            groups.add((entry[1],entry[2]));valid+=1
            if not isinstance(body.get('tick'),int) or body['tick']<=cm['tick']:
                return finish('WITNESS_BEFORE_COMMIT')
        # A shared admin OR a shared upstream is not distinct ancestry.
        admins=[v[1] for v in conflicts];origins=[v[2] for v in conflicts]
        if valid<self.trust.required or len(set(admins))<self.trust.required or len(set(origins))<self.trust.required:
            return finish('INSUFFICIENT_DECLARED_CUSTODY',signatures=valid)
        if not verify(self.trust.principal['reveal'],reveal):return finish('BAD_REVEAL_SIGNATURE')
        rv=reveal['body']
        if rv.get('type')!='reveal' or rv.get('task_hash')!=task['task_hash']:return finish('REVEAL_TASK_MISMATCH')
        if not isinstance(rv.get('tick'),int) or not isinstance(now,int):return finish('BAD_TIME')
        if rv['tick']>now:return finish('FUTURE_REVEAL')
        if any(w['body']['tick']>=rv['tick'] for w in witnesses):return finish('REVEAL_BEFORE_WITNESS')
        disclosure=rv.get('first_disclosure_tick')
        if not isinstance(disclosure,int):return finish('MISSING_DISCLOSURE_HISTORY')
        if disclosure<max(w['body']['tick'] for w in witnesses):return finish('PREMATURE_DISCLOSURE_REPORTED')
        try: expected=commitment(task['task_hash'],rv['seed'])
        except (ValueError,KeyError,TypeError):return finish('BAD_SEED')
        if expected!=cm['seed_commitment']:return finish('COMMITMENT_MISMATCH')
        if self.db.execute('SELECT 1 FROM reveals WHERE task=? AND commitment=?',(task['task_hash'],expected)).fetchone():return finish('REPLAY')
        self.db.execute('INSERT INTO reveals VALUES(?,?)',(task['task_hash'],expected));self.db.commit()
        return finish('WITNESSED_REVEAL_FIXTURE',witnesses=valid,commitment=expected,claim='no proof of seed secrecy or real-world time')

def fixture(witness_count=3, shared_origin=False, disclose_early=False):
    principals={k:deterministic_key(k) for k in ['task','commit','reveal']}
    witness_keys={k:deterministic_key(k) for k in ['A','B','C']}
    trust=Trust({k:v.public_key() for k,v in principals.items()},
                {k:(v.public_key(),'admin'+k,('origin0' if shared_origin else 'origin'+k)) for k,v in witness_keys.items()})
    task_hash=sha('task: deterministic processing sample')
    seed=secrets.token_hex(32)
    c=commitment(task_hash,seed)
    freeze=signed(principals['task'],{'type':'freeze','task_hash':task_hash,'tick':100})
    manifest=signed(principals['commit'],{'type':'commit','task_hash':task_hash,'seed_commitment':c,'tick':110})
    witnesses=[signed(witness_keys[k],{'type':'witness','witness':k,'task_hash':task_hash,'seed_commitment':c,'commit_tick':110,'tick':120+i}) for i,k in enumerate('ABC'[:witness_count])]
    reveal=signed(principals['reveal'],{'type':'reveal','task_hash':task_hash,'seed':seed,'tick':140,'first_disclosure_tick':115 if disclose_early else 135})
    return trust,freeze,manifest,witnesses,reveal

def demo():
    trust,freeze,manifest,witnesses,reveal=fixture()
    a=Auditor(':memory:',trust)
    valid=a.evaluate(freeze,manifest,witnesses,reveal,150)
    replay=a.evaluate(freeze,manifest,witnesses,reveal,151)
    a.close()
    trust2,fr2,cm2,ws2,rv2=fixture(disclose_early=True)
    b=Auditor(':memory:',trust2)
    leaked=b.evaluate(fr2,cm2,ws2,rv2,150)
    b.close()
    return {'experiment':'JANE-191','valid':valid['status'],'replay':replay['status'],'reported_early_disclosure':leaked['status'],'custody_independence':'UNVERIFIED_FIXTURE','active_parent':'FROZEN'}
if __name__=='__main__':print(json.dumps(demo(),indent=2))
