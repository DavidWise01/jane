"""JANE 219 — signed instrument enrollment audit, synthetic fixture only."""
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def canon(x): return json.dumps(x, sort_keys=True, separators=(',', ':')).encode()
def digest(x): return hashlib.sha256(canon(x)).hexdigest()
def fixture_key(name): return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('jane219-fixture:'+name).encode()).digest())
def public(name): return fixture_key(name).public_key().public_bytes_raw().hex()
def sign(body, key_name): return {'body':body, 'signature':fixture_key(key_name).sign(canon(body)).hex()}
def verify(item, public_hex):
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex)).verify(bytes.fromhex(item['signature']), canon(item['body']))
        return True
    except (ValueError, TypeError, KeyError, InvalidSignature, AttributeError): return False

@dataclass(frozen=True)
class Policy:
    min_instruments: int = 2
    max_lag: int = 20

class FLAY219:
    def __init__(self, path=':memory:', policy=Policy(), trusted_issuers=None):
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS audits (nonce TEXT PRIMARY KEY, verdict TEXT NOT NULL, evidence_hash TEXT NOT NULL)')
        self.db.commit()
        self.policy=policy
        self.trusted_issuers=dict(trusted_issuers or {'enrollment-authority':public('enrollment-authority')})
    def close(self):
        if self.db is not None:self.db.close();self.db=None
    def __del__(self):self.close()
    def record(self, nonce, verdict, **detail):
        if not isinstance(nonce,str) or len(nonce)<8 or len(nonce)>256:return {'verdict':'INVALID_NONCE'}
        if self.db.execute('SELECT 1 FROM audits WHERE nonce=?',(nonce,)).fetchone():return {'verdict':'REPLAY_CHALLENGE'}
        result={'verdict':verdict,'nonce':nonce,**detail}
        self.db.execute('INSERT INTO audits VALUES(?,?,?)',(nonce,verdict,digest(result)))
        self.db.commit()
        return result
    def audit(self, challenge, acquisitions, enrollments, revocations=()):
        try: return self._audit(challenge,acquisitions,enrollments,revocations)
        except (KeyError,TypeError,ValueError,OverflowError,IndexError):
            try:return self.record(challenge['body']['nonce'],'MALFORMED_EVIDENCE')
            except (KeyError,TypeError):return {'verdict':'MALFORMED_EVIDENCE'}
    def _audit(self,challenge,acquisitions,enrollments,revocations):
        c=challenge['body']; nonce=c['nonce']
        if not verify(challenge,public('challenger')):return self.record(nonce,'CHALLENGE_SIGNATURE_INVALID')
        if not (isinstance(acquisitions,(tuple,list)) and isinstance(enrollments,(tuple,list)) and isinstance(revocations,(tuple,list))):raise ValueError()
        if not (c['freeze']<c['release']<=c['deadline']):return self.record(nonce,'INVALID_CHRONOLOGY')
        records={}
        for item in enrollments:
            b=item['body']; issuer=b['issuer']; dev=b['device_id']
            if issuer not in self.trusted_issuers or not verify(item,self.trusted_issuers[issuer]):return self.record(nonce,'UNTRUSTED_ENROLLMENT_ISSUER')
            if dev in records:return self.record(nonce,'DUPLICATE_ENROLLMENT')
            if not (isinstance(b['public_key'],str) and len(bytes.fromhex(b['public_key']))==32):return self.record(nonce,'INVALID_DEVICE_KEY')
            if not (b['not_before']<b['not_after']):return self.record(nonce,'INVALID_ENROLLMENT_WINDOW')
            records[dev]=b
        revoked={}
        for item in revocations:
            b=item['body'];issuer=b['issuer']
            if issuer not in self.trusted_issuers or not verify(item,self.trusted_issuers[issuer]):return self.record(nonce,'INVALID_REVOCATION')
            if b['device_id'] in revoked:return self.record(nonce,'CONFLICTING_REVOCATIONS')
            revoked[b['device_id']]=b['effective_at']
        identities=set(); operators=set(); sensors=set(); services=set(); roots=set(); capture_ids=set()
        for item in acquisitions:
            b=item['body'];dev=b['device_id']
            if dev not in records:return self.record(nonce,'SELF_DECLARED_INSTRUMENT')
            e=records[dev]
            if not verify(item,e['public_key']):return self.record(nonce,'INSTRUMENT_SIGNATURE_INVALID')
            if b['nonce']!=nonce or b['content_hash']!=c['expected_hash']:return self.record(nonce,'RESPONSE_MISMATCH')
            t=b['capture']
            if not (c['release']<=t<=c['deadline']) or t-c['release']>self.policy.max_lag:return self.record(nonce,'INVALID_CAPTURE_CHRONOLOGY')
            if not (e['not_before']<=t<e['not_after']):return self.record(nonce,'ENROLLMENT_EXPIRED_OR_NOT_YET_VALID')
            if dev in revoked and t>=revoked[dev]:return self.record(nonce,'REVOKED_INSTRUMENT')
            if b['capture_id'] in capture_ids:return self.record(nonce,'DUPLICATE_CAPTURE')
            capture_ids.add(b['capture_id'])
            if any(v in seen for v,seen in ((dev,identities),(e['operator'],operators),(e['sensor'],sensors),(e['service'],services),(e['root'],roots))):
                return self.record(nonce,'SHARED_INSTRUMENT_ANCESTRY')
            identities.add(dev);operators.add(e['operator']);sensors.add(e['sensor']);services.add(e['service']);roots.add(e['root'])
        if len(identities)<self.policy.min_instruments:return self.record(nonce,'INSUFFICIENT_ENROLLED_INSTRUMENTS',count=len(identities))
        return self.record(nonce,'DECLARED_ENROLLMENT_CHAIN_CONSISTENT_FIXTURE',count=len(identities),physical_identity_proven=False)
    def verify_log(self):
        rows=self.db.execute('SELECT nonce,verdict,evidence_hash FROM audits ORDER BY rowid').fetchall()
        return len(rows)==len({r[0] for r in rows}) and all(len(r[2])==64 and all(ch in '0123456789abcdef' for ch in r[2]) for r in rows)


def fixture(kind='valid',nonce='219-fixture-nonce-0001'):
    c=sign({'nonce':nonce,'freeze':100,'release':120,'deadline':150,'expected_hash':digest('orange-pulse')},'challenger')
    enrollments=[]; acquisitions=[]; revocations=[]
    for i in range(2):
        dev=f'instrument-{i}'
        record={'issuer':'enrollment-authority','device_id':dev,'public_key':public(dev),'not_before':50,'not_after':200,'operator':f'operator-{i}','sensor':f'sensor-{i}','service':f'service-{i}','root':f'root-{i}'}
        if kind=='shared':record['service']='service-0'
        if kind=='expired':record['not_after']=125
        if kind=='substituted' and i==1:record['public_key']=public('attacker')
        if kind=='issuer' and i==1:record['issuer']='fake-issuer'
        enrollments.append(sign(record, 'enrollment-authority' if kind!='issuer' or i==0 else 'fake-issuer'))
        a={'device_id':dev,'nonce':nonce,'capture':130+i,'capture_id':f'capture-{i}','content_hash':c['body']['expected_hash']}
        if kind=='stale':a['capture']=119
        if kind=='mismatch':a['content_hash']=digest('fake-image')
        if kind=='duplicate':a['capture_id']='capture-0'
        acquisitions.append(sign(a,dev))
    if kind=='self':enrollments=[]
    if kind=='revoked':revocations.append(sign({'issuer':'enrollment-authority','device_id':'instrument-1','effective_at':125},'enrollment-authority'))
    if kind=='forged':acquisitions[1]['signature']='00'*64
    if kind=='insufficient':acquisitions=acquisitions[:1]
    return c,acquisitions,enrollments,revocations

if __name__=='__main__':
    out={}
    for kind in ('valid','self','shared','expired','substituted','issuer','stale','mismatch','duplicate','revoked','forged','insufficient'):
        f=FLAY219();out[kind]=f.audit(*fixture(kind,nonce=f'219-{kind}-fixture-0001'));f.close()
    print(json.dumps({'experiment':219,'invariant':'Self-Signed Instrument Identity != Trusted Instrument Identity','fixture_only':True,'results':out},indent=2))
