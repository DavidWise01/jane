"""JANE 170 — signed sensor observations and conservative clock-condition selection.

Synthetic fixture keys and ancestry: not proof of physical measurement or real-world independence.
"""
import hashlib, json, sqlite3
from dataclasses import dataclass
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

PROFILES = {'normal': 10, 'hot_battery': 120, 'holdover': 250}  # drift ppm, fixture policy
DOMAIN = 'JANE-170-SENSOR-OBSERVATION-v1'

def canonical(obj): return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
def digest(obj): return hashlib.sha256(canonical(obj)).hexdigest()

def claim(sensor, root, admin, condition, observed_ms, uncertainty_ms, nonce, clock='chronos_fixture'):
    return {'domain':DOMAIN, 'sensor':sensor, 'root':root, 'admin':admin,
            'condition':condition,'observed_ms':observed_ms,'uncertainty_ms':uncertainty_ms,
            'nonce':nonce,'clock':clock}

def sign(private, body): return {'claim': body, 'signature': private.sign(canonical(body)).hex()}

@dataclass(frozen=True)
class Policy:
    max_age_ms:int=300000
    future_skew_ms:int=30000
    min_roots:int=3
    max_uncertainty_ms:int=10000
    def __post_init__(self):
        for value in (self.max_age_ms,self.future_skew_ms,self.max_uncertainty_ms):
            if type(value) is not int or value<0:raise ValueError('invalid policy')
        if type(self.min_roots) is not int or self.min_roots<1:raise ValueError('invalid quorum')

class SensorAudit:
    def __init__(self, db, keys, policy=Policy()):
        """keys: sensor_id -> (Ed25519 public key, expected custody root, expected administrator)."""
        self.db=sqlite3.connect(str(db))
        self.db.execute('CREATE TABLE IF NOT EXISTS accepted(sensor TEXT, nonce TEXT, digest TEXT, PRIMARY KEY(sensor,nonce))')
        self.db.execute('CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, prev TEXT, kind TEXT, payload TEXT, head TEXT)')
        self.db.commit()
        self.keys=keys;self.policy=policy
        self.active='frozen_parent'
    def close(self): self.db.close()
    def _record(self,kind,payload):
        row=self.db.execute('SELECT head FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        prev=row[0] if row else '0'*64
        data={'kind':kind,'payload':payload,'prev':prev}
        h=digest(data)
        self.db.execute('INSERT INTO events(prev,kind,payload,head) VALUES(?,?,?,?)',(prev,kind,json.dumps(payload,sort_keys=True),h))
        self.db.commit()
        return h
    def ledger(self):
        prev='0'*64
        for p,k,body,h in self.db.execute('SELECT prev,kind,payload,head FROM events ORDER BY seq'):
            if p!=prev or h!=digest({'kind':k,'payload':json.loads(body),'prev':p}):return 'TAMPERED'
            prev=h
        return 'VALID_LOCAL_CHAIN'
    def check(self, packets, now_ms, expected_condition=None):
        if type(now_ms) is not int:raise ValueError('now_ms must be integer')
        observations=[];rejects=[];roots={};admins={};seen_nonce=set()
        for packet in packets:
            try:
                body=packet['claim']; sensor=body['sensor']
                if sensor not in self.keys:raise ValueError('UNKNOWN_SENSOR')
                pub,root,admin=self.keys[sensor]
                if body.get('domain')!=DOMAIN:raise ValueError('BAD_DOMAIN')
                if body.get('root')!=root or body.get('admin')!=admin:raise ValueError('IDENTITY_MISMATCH')
                for field in ('observed_ms','uncertainty_ms'):
                    if type(body.get(field)) is not int:raise ValueError('MALFORMED_TIME')
                if body['uncertainty_ms']<0 or body['uncertainty_ms']>self.policy.max_uncertainty_ms:raise ValueError('UNSUPPORTED_UNCERTAINTY')
                if type(body.get('nonce')) is not str or not body['nonce']:raise ValueError('BAD_NONCE')
                if type(body.get('condition')) is not str or not body['condition']:raise ValueError('UNKNOWN_CONDITION')
                try:pub.verify(bytes.fromhex(packet['signature']),canonical(body))
                except (InvalidSignature, ValueError, KeyError, TypeError):raise ValueError('BAD_SIGNATURE')
                if (sensor,body['nonce']) in seen_nonce or self.db.execute('SELECT 1 FROM accepted WHERE sensor=? AND nonce=?',(sensor,body['nonce'])).fetchone():raise ValueError('REPLAY')
                seen_nonce.add((sensor,body['nonce']))
                earliest=body['observed_ms']-body['uncertainty_ms']
                latest=body['observed_ms']+body['uncertainty_ms']
                if earliest>now_ms+self.policy.future_skew_ms:raise ValueError('FUTURE_OBSERVATION')
                if latest<now_ms-self.policy.max_age_ms:raise ValueError('STALE_OBSERVATION')
                if root in roots and roots[root]!=sensor:raise ValueError('SHARED_CUSTODY_ROOT')
                if admin in admins and admins[admin]!=root:raise ValueError('SHARED_ADMINISTRATION')
                roots[root]=sensor;admins[admin]=root
                observations.append(body)
                self.db.execute('INSERT INTO accepted(sensor,nonce,digest) VALUES(?,?,?)',(sensor,body['nonce'],digest(body)))
            except (KeyError,TypeError,ValueError) as exc:
                rejects.append({'reason':str(exc),'sensor':packet.get('claim',{}).get('sensor','?') if isinstance(packet,dict) else '?'})
        conditions=sorted(set(o['condition'] for o in observations))
        fresh=len(observations)
        quorum=(fresh>=self.policy.min_roots and len(roots)>=self.policy.min_roots and len(admins)>=self.policy.min_roots)
        if not quorum: status='INSUFFICIENT_PROVENANCE'
        elif len(conditions)>1: status='SENSOR_CONFLICT'
        elif conditions[0] not in PROFILES:status='UNKNOWN_CONDITION'
        elif expected_condition is not None and conditions[0]!=expected_condition:status='PROFILE_CHANGED'
        else:status='CONDITION_SUPPORTED_FIXTURE'
        # No favorable default under conflict, uncertainty, insufficient sources, or profile change.
        safe_ppm=PROFILES[conditions[0]] if status=='CONDITION_SUPPORTED_FIXTURE' else None
        output={'version':'JANE-170','status':status,'accepted':fresh,'required':self.policy.min_roots,
                'roots':sorted(roots),'administrators':sorted(admins),'reported_conditions':conditions,
                'rejections':rejects,'allowed_drift_ppm':safe_ppm,'recalibration_required':safe_ppm is None,
                'independent_operators_verified':False,'physical_condition_verified':False,
                'parent':'frozen_parent','jane_decision':'UNDECIDED','learning_applied':False}
        output['digest']=digest(output)
        self._record('SENSOR_AUDIT',{'result_digest':output['digest'],'status':status,'rejections':rejects})
        return output

def fixture():
    seeds=[bytes([x])*32 for x in (3,7,11)]
    priv=[Ed25519PrivateKey.from_private_bytes(x) for x in seeds]
    keys={f'sensor{i}':(p.public_key(),f'root{i}',f'admin{i}') for i,p in enumerate(priv,1)}
    return priv,keys

def sample(priv, conditions=('normal','normal','normal'), now_ms=1000000, suffix='first'):
    return [sign(p,claim(f'sensor{i}',f'root{i}',f'admin{i}',c,now_ms,3,f'{suffix}:{i}'))
            for i,(p,c) in enumerate(zip(priv,conditions),1)]

def demo():
    import tempfile
    priv,keys=fixture()
    with tempfile.TemporaryDirectory() as tmp:
        a=SensorAudit(Path(tmp)/'audit.db',keys)
        good=a.check(sample(priv,suffix='good'),1000000)
        bad=a.check(sample(priv,('normal','hot_battery','normal'),suffix='conflict'),1000000)
        missing=a.check(sample(priv,suffix='missing')[:2],1000000)
        unknown=a.check(sample(priv,('mystery','mystery','mystery'),suffix='unknown'),1000000)
        ledger=a.ledger();a.close()
    return {'case':'synthetic signed sensor audit','valid':good,'conflict':bad,
            'missing':missing,'unknown':unknown,'ledger':ledger}
if __name__=='__main__': print(json.dumps(demo(),indent=2))