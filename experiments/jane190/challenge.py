"""JANE 190: cryptographically bound challenge-disclosure timeline; fixture-only claims."""
import hashlib, json, sqlite3, secrets
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def sha(v): return hashlib.sha256(v if isinstance(v,bytes) else canonical(v)).hexdigest()
def pub(sk): return sk.public_key().public_bytes_raw().hex()
def sign(sk,v): return sk.sign(canonical(v)).hex()
def verify(key,body,sig):
    try: Ed25519PublicKey.from_public_bytes(bytes.fromhex(key)).verify(bytes.fromhex(sig),canonical(body));return True
    except (InvalidSignature,ValueError,TypeError): return False

def signed(role, body,sk): return dict(role=role,body=body,public_key=pub(sk),signature=sign(sk,body))
@dataclass(frozen=True)
class Policy:
    max_lag:int=300
    max_span:int=120
    def __post_init__(self):
        if not (1<=self.max_lag<=10000 and 1<=self.max_span<=10000):raise ValueError('invalid policy')

class Audit:
    def __init__(self,path,keys,policy=Policy()):
        self.db=sqlite3.connect(path)
        self.db.execute('create table if not exists used (nonce text primary key, task text not null)')
        self.db.execute('create table if not exists events (id integer primary key, kind text, payload text, prev text, head text)')
        self.db.commit()
        self.keys=keys;self.policy=policy;self.active='frozen_parent'
    def close(self):self.db.close()
    def _append(self,kind,payload):
        row=self.db.execute('select head from events order by id desc limit 1').fetchone(); prev=row[0] if row else '0'*64
        head=sha(dict(kind=kind,payload=payload,prev=prev))
        self.db.execute('insert into events(kind,payload,prev,head) values(?,?,?,?)',(kind,json.dumps(payload,sort_keys=True),prev,head));self.db.commit()
    def audit_chain(self,external_head=None):
        prev='0'*64
        for kind,txt,p,h in self.db.execute('select kind,payload,prev,head from events order by id'):
            if p!=prev or h!=sha(dict(kind=kind,payload=json.loads(txt),prev=prev)):return 'TAMPERED'
            prev=h
        return 'EXTERNAL_HEAD_MISMATCH' if external_head is not None and external_head!=prev else 'VALID_LOCAL_CHAIN'
    def accept(self,task,challenge,disclosure,execution,effects,now):
        """Receipt timestamps are signed claims. A leaked nonce can only be detected if logged evidence admits it."""
        def finish(status):
            self._append('REVIEW',dict(status=status,task=task.get('body',{}).get('task_hash'),nonce=challenge.get('body',{}).get('nonce')))
            return status
        items=[(task,'task'),(challenge,'challenger'),(disclosure,'challenger'),(execution,'executor')]+[(x,'observer') for x in effects]
        for item,role in items:
            if item.get('role')!=role or item.get('public_key')!=self.keys.get(role) or not verify(item.get('public_key',''),item.get('body',{}),item.get('signature','')):return finish('BAD_SIGNATURE_OR_ROLE')
        t,c,d,e=[v['body'] for v in (task,challenge,disclosure,execution)]
        try:
            if any(type(x)!=int for x in [t['at'],c['at'],d['at'],e['at'],now]):return finish('BAD_CHRONOS')
            nonce=c['nonce']
            if len(nonce)!=32 or any(a not in '0123456789abcdef' for a in nonce):return finish('BAD_NONCE')
            if t['task_hash']!=sha(t['task']) or c['task_hash']!=t['task_hash'] or d['task_hash']!=t['task_hash'] or e['task_hash']!=t['task_hash']:return finish('TASK_BINDING_CONFLICT')
            if d['nonce']!=nonce or e['nonce']!=nonce or c['commitment']!=sha({'task_hash':t['task_hash'],'nonce':nonce}):return finish('CHALLENGE_BINDING_CONFLICT')
            if t['at']>=c['at'] or c['at']>d['at'] or d['at']>=e['at']:return finish('CAUSAL_ORDER_VIOLATION')
            if d.get('leaked_at') is not None and d['leaked_at']<d['at']:return finish('PREMATURE_DISCLOSURE_REPORTED')
            if e['at']-d['at']>self.policy.max_span:return finish('EXECUTION_WINDOW_EXCEEDED')
            if now<e['at'] or now-e['at']>self.policy.max_lag:return finish('STALE_OR_FUTURE_EXECUTION')
            if not effects:return finish('UNCORROBORATED_EXECUTION')
            for x in effects:
                b=x['body']
                if b.get('nonce')!=nonce or b.get('task_hash')!=t['task_hash'] or b.get('output_hash')!=e.get('output_hash'):return finish('EFFECT_CONFLICT')
                if type(b.get('at'))!=int or b['at']<e['at'] or b['at']>now:return finish('EFFECT_CHRONOS_CONFLICT')
            if len({x['body'].get('source_root') for x in effects})!=len(effects):return finish('SHARED_OBSERVER_ANCESTRY')
            if len(effects)<2:return finish('INSUFFICIENT_OBSERVERS')
        except (KeyError,TypeError,AttributeError):return finish('MALFORMED_EVIDENCE')
        try:
            with self.db:
                self.db.execute('insert into used(nonce,task) values(?,?)',(nonce,t['task_hash']))
        except sqlite3.IntegrityError:return finish('REPLAY')
        return finish('CHRONOLOGY_CONSISTENT_FIXTURE')

def fixture(nonce='0123456789abcdef0123456789abcdef',leaked_at=None):
    keys={r:Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('jane190:'+r).encode()).digest()) for r in ['task','challenger','executor','observer']}
    task_data={'program':'add','input':7,'value':3}; th=sha(task_data)
    task=signed('task',dict(task=task_data,task_hash=th,at=100),keys['task'])
    challenge=signed('challenger',dict(task_hash=th,nonce=nonce,at=110,commitment=sha({'task_hash':th,'nonce':nonce})),keys['challenger'])
    disclosure=signed('challenger',dict(task_hash=th,nonce=nonce,at=120,leaked_at=leaked_at),keys['challenger'])
    execution=signed('executor',dict(task_hash=th,nonce=nonce,at=130,output_hash=sha({'out':10,'nonce':nonce})),keys['executor'])
    effects=[signed('observer',dict(task_hash=th,nonce=nonce,at=140+i,output_hash=execution['body']['output_hash'],source_root=f'source-{i}'),keys['observer']) for i in range(2)]
    return {r:pub(sk) for r,sk in keys.items()},[task,challenge,disclosure,execution,effects]

def demo():
    import tempfile,os
    with tempfile.TemporaryDirectory() as td:
        keys,pack=fixture();db=os.path.join(td,'audit.db'); a=Audit(db,keys)
        valid=a.accept(*pack,now=150);again=a.accept(*pack,now=150);chain=a.audit_chain();a.close()
        a=Audit(db,keys);restart=a.accept(*pack,now=150);a.close()
        keys,pack=fixture(leaked_at=115);b=Audit(':memory:',keys);leak=b.accept(*pack,now=150);b.close()
    return dict(experiment='JANE-190',valid=valid,replay=again,replay_after_restart=restart,reported_leak=leak,chain=chain,active='frozen_parent',independent_witnesses_verified=False,physical_execution_verified=False)
if __name__=='__main__': print(json.dumps(demo(),indent=2))