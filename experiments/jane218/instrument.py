"""JANE 218: fixture-only instrument ancestry and acquisition-attestation audit."""
import hashlib, json, sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


def canon(v): return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def digest(v): return hashlib.sha256(canon(v)).hexdigest()
def key(i): return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('JANE218-fixture-'+i).encode()).digest())
def signed(body, signer): return {'body':body,'signer':signer,'signature':key(signer).sign(canon(body)).hex()}
def valid(item):
    try:
        Ed25519PublicKey.from_public_bytes(key(item['signer']).public_key().public_bytes_raw()).verify(bytes.fromhex(item['signature']),canon(item['body']))
        return True
    except (InvalidSignature,ValueError,TypeError,KeyError,AttributeError): return False

@dataclass(frozen=True)
class Policy:
    min_external: int = 2
    max_capture_lag: int = 20

class FLAY218:
    def __init__(self,path=':memory:',policy=Policy()):
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS attempts (nonce TEXT PRIMARY KEY, verdict TEXT NOT NULL, evidence TEXT NOT NULL)')
        self.db.commit()
        self.policy=policy
    def close(self):
        if getattr(self,"db",None) is not None:
            self.db.close();self.db=None
    def __del__(self):self.close()
    def audit(self,challenge,executor,acquisitions):
        try: return self._audit(challenge,executor,acquisitions)
        except (KeyError,ValueError,TypeError,OverflowError) as e: return self._store_if_possible(challenge,'MALFORMED_EVIDENCE',{'reason':type(e).__name__})
    def _store_if_possible(self,challenge,verdict,detail):
        try: nonce=challenge['body']['nonce']
        except (KeyError,TypeError): return {'verdict':verdict,**detail}
        if not isinstance(nonce,str) or not nonce or len(nonce)>256:return {'verdict':'INVALID_NONCE'}
        if self.db.execute('SELECT 1 FROM attempts WHERE nonce=?',(nonce,)).fetchone():return {'verdict':'REPLAY_CHALLENGE'}
        result={'verdict':verdict,'challenge_nonce':nonce,**detail}
        self.db.execute('INSERT INTO attempts VALUES(?,?,?)',(nonce,verdict,digest(result)))
        self.db.commit()
        return result
    def _audit(self,challenge,executor,acquisitions):
        c=challenge['body']; x=executor['body']
        if not isinstance(acquisitions,list) or not all(isinstance(a,dict) for a in acquisitions):raise ValueError('acquisitions')
        if not valid(challenge) or not valid(executor) or any(not valid(a) for a in acquisitions): return self._store_if_possible(challenge,'SIGNATURE_INVALID',{})
        if challenge['signer']!='challenger' or executor['signer']!='executor':return self._store_if_possible(challenge,'SIGNER_ROLE_INVALID',{})
        nonce=c['nonce']
        if not isinstance(nonce,str) or not (16<=len(nonce)<=256):return {'verdict':'INVALID_NONCE'}
        if c['release']<=c['freeze'] or x['capture']<c['release'] or x['capture']>c['deadline']:
            return self._store_if_possible(challenge,'INVALID_CHRONOLOGY',{})
        if x['nonce']!=nonce or x['pattern']!=c['pattern'] or x['content_hash']!=c['expected_hash']:
            return self._store_if_possible(challenge,'EXECUTOR_MISMATCH',{})
        if not acquisitions:return self._store_if_possible(challenge,'NO_ACQUISITION_EVIDENCE',{})
        roots=set(); sensors=set(); operators=set(); services=set(); capture_ids=set(); external=0
        for a in acquisitions:
            b=a['body']
            if b['nonce']!=nonce or b['content_hash']!=x['content_hash']:
                return self._store_if_possible(challenge,'ACQUISITION_CONTENT_MISMATCH',{})
            if b['capture']<c['release'] or b['capture']>c['deadline'] or abs(b['capture']-x['capture'])>self.policy.max_capture_lag:
                return self._store_if_possible(challenge,'INVALID_ACQUISITION_CHRONOLOGY',{})
            if b['kind'] not in ('external_instrument','software_simulator'):
                return self._store_if_possible(challenge,'UNKNOWN_INSTRUMENT_KIND',{})
            if not b['capture_id'] or b['capture_id'] in capture_ids:
                return self._store_if_possible(challenge,'DUPLICATED_CAPTURE',{})
            capture_ids.add(b['capture_id'])
            if b['root'] in roots or b['sensor'] in sensors or b['operator'] in operators or b['service'] in services:
                return self._store_if_possible(challenge,'SHARED_ACQUISITION_ANCESTRY',{})
            roots.add(b['root']);sensors.add(b['sensor']);operators.add(b['operator']);services.add(b['service'])
            if b['kind']=='external_instrument':external+=1
        if external<self.policy.min_external:
            return self._store_if_possible(challenge,'ONLY_SIMULATED_OR_INSUFFICIENT_INSTRUMENTATION',{'external_claims':external})
        return self._store_if_possible(challenge,'DECLARED_INSTRUMENT_CONSISTENCY_FIXTURE',{'external_claims':external,'root_count':len(roots),'physical_causation_proven':False})

def fixture(kind='independent',nonce='218-fixture-nonce-001'):
    c=signed({'nonce':nonce,'freeze':100,'release':120,'deadline':160,'pattern':'orange-1010','expected_hash':digest('frame-1010')},'challenger')
    x=signed({'nonce':nonce,'capture':132,'pattern':'orange-1010','content_hash':digest('frame-1010')},'executor')
    aa=[]
    for i in range(2):
        b={'nonce':nonce,'content_hash':digest('frame-1010'),'capture':133+i,'capture_id':'capture'+str(i),'kind':'external_instrument','root':'root'+str(i),'sensor':'sensor'+str(i),'operator':'operator'+str(i),'service':'service'+str(i)}
        if kind=='simulated': b['kind']='software_simulator'
        if kind=='shared':b['service']='shared'
        if kind=='copied':b['capture_id']='duplicate'
        if kind=='stale':b['capture']=119
        if kind=='mismatch':b['content_hash']=digest('different')
        aa.append(signed(b,'observer'+str(i)))
    return c,x,aa

if __name__=='__main__':
    out={}
    for typ in ('independent','simulated','shared','copied','stale','mismatch'):
        audit=FLAY218();out[typ]=audit.audit(*fixture(typ));audit.close()
    print(json.dumps({'experiment':218,'invariant':'Valid Response Attestation != Independent Physical Measurement','fixture_only':True,'results':out},indent=2))