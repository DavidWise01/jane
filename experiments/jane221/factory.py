"""JANE 221 | signed factory narrative versus independent production records.
Synthetic cryptographic fixture. No claim of hardware provenance.
"""
import hashlib, json, sqlite3
from dataclasses import dataclass
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

def canonical(v): return json.dumps(v, sort_keys=True, separators=(',',':')).encode()
def digest(v): return hashlib.sha256(canonical(v)).hexdigest()
def key(seed): return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(seed.encode()).digest())
def seal(body, signer): return {'body':body, 'signature':key(signer).sign(canonical(body)).hex()}
def verify(envelope, signer):
    try:
        key(signer).public_key().verify(bytes.fromhex(envelope['signature']),canonical(envelope['body']))
        return True
    except (InvalidSignature, KeyError, TypeError, ValueError): return False

class Audit:
    def __init__(self, location=':memory:'):
        self.db=sqlite3.connect(str(location))
        self.db.execute('CREATE TABLE IF NOT EXISTS events (n INTEGER PRIMARY KEY AUTOINCREMENT, previous TEXT NOT NULL, body TEXT NOT NULL, hash TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS nonces (nonce TEXT PRIMARY KEY)')
        self.db.commit()
    def valid(self):
        previous='0'*64
        for n,p,b,h in self.db.execute('SELECT n,previous,body,hash FROM events ORDER BY n'):
            if p!=previous or digest({'previous':p,'body':json.loads(b)})!=h: return False
            previous=h
        return True
    def record(self,nonce,event):
        if not self.valid():return 'CORRUPT_LOG'
        if self.db.execute('SELECT 1 FROM nonces WHERE nonce=?',(nonce,)).fetchone(): return 'REPLAY'
        prev=self.db.execute('SELECT hash FROM events ORDER BY n DESC LIMIT 1').fetchone()
        prev=prev[0] if prev else '0'*64
        b=canonical(event).decode()
        h=digest({'previous':prev,'body':event})
        with self.db:
            self.db.execute('INSERT INTO nonces VALUES (?)',(nonce,))
            self.db.execute('INSERT INTO events(previous,body,hash) VALUES (?,?,?)',(prev,b,h))
        return None
    def close(self): self.db.close()
    def __del__(self):
        try:self.db.close()
        except Exception:pass

@dataclass(frozen=True)
class Policy:
    min_independent_roots:int=2
    min_production_witnesses:int=2

class FLAY221:
    def __init__(self, audit=None, policy=Policy()): self.audit=audit or Audit();self.policy=policy
    def inspect(self, packet):
        try:
            claim=packet['factory_claim']; order=packet['order']; observes=packet['observations']; checkpoint=packet['checkpoint']
            cb=claim['body']; ob=order['body']; ch=checkpoint['body']
            required=('device','unit','batch','process_hash','timestamp')
            if not all(k in cb for k in required) or not all(k in ob for k in ('device','unit','batch','nonce','timestamp')):return self._result('INVALID_PACKET')
            if not isinstance(ob['nonce'],str) or len(ob['nonce'])<12:return self._result('INVALID_NONCE')
            if not verify(claim,'factory') or not verify(order,'ordering') or not verify(checkpoint,'ledger'):
                return self._result('INVALID_SIGNATURE')
            if not (cb['device']==ob['device']==ch['device'] and cb['unit']==ob['unit']==ch['unit'] and cb['batch']==ob['batch']==ch['batch']): return self._result('IDENTITY_MISMATCH')
            if ch['order_digest']!=digest(ob) or ch['claim_digest']!=digest(cb):return self._result('CHECKPOINT_MISMATCH')
            if not(ob['timestamp']<=cb['timestamp']<=ch['timestamp']):return self._result('INVALID_CHRONOLOGY')
            if not isinstance(observes,list) or not observes: return self._result('NO_PRODUCTION_OBSERVATION')
            roots=set(); devices=set(); signers=set(); timestamps=[]
            for envelope in observes:
                b=envelope['body']; actor=b['actor']
                if actor not in ('w1','w2','w3') or not verify(envelope,actor):return self._result('INVALID_OBSERVER_SIGNATURE')
                if b['device']!=cb['device'] or b['unit']!=cb['unit'] or b['batch']!=cb['batch']:return self._result('OBSERVED_IDENTITY_MISMATCH')
                if b['process_hash']!=cb['process_hash']:return self._result('PROCESS_DISAGREEMENT')
                if b['claim_digest']!=digest(cb):return self._result('OBSERVATION_CLAIM_MISMATCH')
                if b['timestamp']<ob['timestamp'] or b['timestamp']>ch['timestamp']:return self._result('OBSERVATION_TIME_INVALID')
                if b.get('source')!='production_sensor':return self._result('DOCUMENT_ONLY_CORROBORATION')
                if actor in signers:return self._result('DUPLICATE_WITNESS')
                signers.add(actor);roots.add(b['ancestry_root']);devices.add(b['instrument']);timestamps.append(b['timestamp'])
            if len(observes)<self.policy.min_production_witnesses:return self._result('INSUFFICIENT_WITNESSES')
            if len(roots)<self.policy.min_independent_roots or len(devices)<self.policy.min_independent_roots:return self._result('SHARED_PRODUCTION_ANCESTRY')
            if ch['observer_digests']!=sorted(digest(e['body']) for e in observes):return self._result('CHECKPOINT_MISMATCH')
            event={'order':digest(ob),'claim':digest(cb),'checkpoint':digest(ch),'observations':sorted(digest(e['body']) for e in observes)}
            state=self.audit.record(ob['nonce'],event)
            return self._result(state or 'DECLARED_PRODUCTION_OBSERVATIONS_CONSISTENT_FIXTURE',roots=sorted(roots),event_hash=digest(event))
        except (TypeError,ValueError,KeyError,AttributeError): return self._result('INVALID_PACKET')
    @staticmethod
    def _result(code,**details):return {'verdict':code,'physical_manufacture_verified':False,'jane_parent_mutated':False,**details}

def fixture(mode='consistent',nonce='challenge-221-0001'):
    order={'device':'JANE-SENSOR','unit':'SN-221-A','batch':'B-7','nonce':nonce,'timestamp':100}
    factory={'device':order['device'],'unit':order['unit'],'batch':order['batch'],'process_hash':'3a'*32,'timestamp':110}
    witnesses=[]
    for i in (1,2):
        b={'actor':f'w{i}','device':order['device'],'unit':order['unit'],'batch':order['batch'],
           'process_hash':factory['process_hash'],'claim_digest':digest(factory),'source':'production_sensor',
           'ancestry_root':f'physical-root-{i}','instrument':f'production-line-{i}','timestamp':120+i}
        witnesses.append(seal(b,f'w{i}'))
    if mode=='factory_only':witnesses=[]
    elif mode=='document_copies':
        for w in witnesses:w['body']['source']='factory_document';w['signature']=seal(w['body'],w['body']['actor'])['signature']
    elif mode=='shared_root':
        witnesses[1]['body']['ancestry_root']=witnesses[0]['body']['ancestry_root'];witnesses[1]=seal(witnesses[1]['body'],'w2')
    elif mode=='shared_instrument':
        witnesses[1]['body']['instrument']=witnesses[0]['body']['instrument'];witnesses[1]=seal(witnesses[1]['body'],'w2')
    elif mode=='wrong_process':
        witnesses[1]['body']['process_hash']='ff'*32;witnesses[1]=seal(witnesses[1]['body'],'w2')
    elif mode=='late_sensor':
        witnesses[1]['body']['timestamp']=160;witnesses[1]=seal(witnesses[1]['body'],'w2')
    elif mode=='forged_observer':witnesses[1]['signature']='00'*64
    elif mode=='duplicate_witness': witnesses[1]=dict(witnesses[0])
    checkpoint={'device':order['device'],'unit':order['unit'],'batch':order['batch'],'order_digest':digest(order),'claim_digest':digest(factory),'observer_digests':sorted(digest(w['body']) for w in witnesses),'timestamp':150}
    return {'order':seal(order,'ordering'),'factory_claim':seal(factory,'factory'),'observations':witnesses,'checkpoint':seal(checkpoint,'ledger')}

if __name__=='__main__':
    import sys
    scenarios=('consistent','factory_only','document_copies','shared_root','shared_instrument','wrong_process','late_sensor','forged_observer','duplicate_witness')
    out={m:FLAY221().inspect(fixture(m)) for m in scenarios}
    print(json.dumps({'experiment':221,'invariant':'Signed Manufacturing History != Independent Evidence of Manufacture','scenarios':out,'limitations':'All keys, witnesses, manufacturing records, and sensors are synthetic. No physical manufacture verified.'},indent=2))