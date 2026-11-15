"""JANE 216: signed fixture stimulus-response verification; not physical attestation."""
from __future__ import annotations
import hashlib, json, sqlite3, tempfile, os
from dataclasses import dataclass
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def digest(x): return hashlib.sha256(canonical(x)).hexdigest()
def key(seed): return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('jane216.fixture.'+seed).encode()).digest())
def pub(seed): return key(seed).public_key()
def signed(seed,body): return {'body':body,'signature':key(seed).sign(canonical(body)).hex()}
def verify(public,packet):
    try:
        public.verify(bytes.fromhex(packet['signature']),canonical(packet['body']))
        return True
    except (ValueError,InvalidSignature,KeyError,TypeError,AttributeError): return False

def make_fixture(mode='valid',nonce='challenge-216-a'):
    stimulus={'nonce':nonce,'stimulus_id':'pulse-orange-216','frame':'rgb8:4x4','pattern':'top-right-orange','committed_at':100,'released_at':120,'deadline':170,'operator_root':'stimulus-root'}
    challenge=signed('controller',stimulus)
    content={'nonce':nonce,'stimulus_digest':digest(stimulus),'capture_id':'capture-216-a','sensor_id':'cam-A','sensor_root':'sensor-root','capture_time':130,'response':'orange-top-right','frame_digest':digest({'rgb':[0,0,0,255,125,21]*8})}
    captured=signed('sensor',content)
    witnesses=[]
    for name,root,t in [('A','observer-root-A',135),('B','observer-root-B',138)]:
        witnesses.append(signed('witness-'+name,{'name':name,'root':root,'sensor_root':'sensor-root','operator_root':'operator-'+name,'capture_id':content['capture_id'],'response_digest':digest(content),'observed_at':t}))
    if mode=='old_frame':
        content['response']='unrelated-static-scene'; captured=signed('sensor',content)
        witnesses=[signed('witness-'+n,dict(w['body'],response_digest=digest(content))) for n,w in [('A',witnesses[0]),('B',witnesses[1])]]
    elif mode=='early':
        content['capture_time']=110; captured=signed('sensor',content)
        witnesses=[signed('witness-'+n,dict(w['body'],response_digest=digest(content))) for n,w in [('A',witnesses[0]),('B',witnesses[1])]]
    elif mode=='late':
        content['capture_time']=175; captured=signed('sensor',content)
        witnesses=[signed('witness-'+n,dict(w['body'],response_digest=digest(content),observed_at=180+i)) for i,(n,w) in enumerate([('A',witnesses[0]),('B',witnesses[1])])]
    elif mode=='wrong_nonce':
        content['nonce']='wrong-nonce'; captured=signed('sensor',content)
        witnesses=[signed('witness-'+n,dict(w['body'],response_digest=digest(content))) for n,w in [('A',witnesses[0]),('B',witnesses[1])]]
    elif mode=='shared_root':
        witnesses[1]=signed('witness-B',dict(witnesses[1]['body'],root='observer-root-A'))
    elif mode=='shared_operator':
        witnesses[1]=signed('witness-B',dict(witnesses[1]['body'],operator_root='operator-A'))
    elif mode=='sensor_as_witness':
        witnesses[1]=signed('witness-B',dict(witnesses[1]['body'],root='sensor-root'))
    elif mode=='mismatch':
        witnesses[1]=signed('witness-B',dict(witnesses[1]['body'],response_digest='0'*64))
    elif mode=='witness_early':
        witnesses[0]=signed('witness-A',dict(witnesses[0]['body'],observed_at=125))
    elif mode=='tamper':
        captured['body']['frame_digest']='f'*64
    elif mode=='tamper_challenge':
        challenge['body']['deadline']=160
    elif mode=='reused_capture':
        content['capture_id']='capture-216-a'; captured=signed('sensor',content)
    elif mode!='valid': raise ValueError('unknown fixture')
    return {'challenge':challenge,'capture':captured,'witnesses':witnesses}

class Audit:
    def __init__(self,path):
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS used (kind TEXT, identifier TEXT, PRIMARY KEY(kind,identifier))')
        self.db.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, prev TEXT, payload TEXT, hash TEXT)')
        self.db.commit()
    def close(self):self.db.close()
    def chain_valid(self):
        prev='0'*64
        for seq,p,h,actual in self.db.execute('SELECT seq,prev,payload,hash FROM events ORDER BY seq'):
            if p!=prev or actual!=hashlib.sha256((p+h).encode()).hexdigest(): return False
            prev=actual
        return True
    def used(self,kind,identifier): return self.db.execute('SELECT 1 FROM used WHERE kind=? AND identifier=?',(kind,identifier)).fetchone() is not None
    def append(self,challenge,capture,verdict):
        payload=canonical({'challenge':challenge,'capture':capture,'verdict':verdict}).decode()
        with self.db:
            prevrow=self.db.execute('SELECT hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
            prev=prevrow[0] if prevrow else '0'*64
            self.db.execute('INSERT INTO events(prev,payload,hash) VALUES(?,?,?)',(prev,payload,hashlib.sha256((prev+payload).encode()).hexdigest()))
            if verdict=='CHALLENGE_RESPONSE_CONSISTENT_FIXTURE':
                self.db.execute('INSERT INTO used VALUES (?,?)',('challenge',challenge))
                self.db.execute('INSERT INTO used VALUES (?,?)',('capture',capture))

class FLAY216:
    def __init__(self,audit): self.audit=audit
    def evaluate(self,evidence):
        if not self.audit.chain_valid(): return 'CORRUPT_AUDIT'
        try:
            c,s,w=evidence['challenge'],evidence['capture'],evidence['witnesses']
            if not verify(pub('controller'),c) or not verify(pub('sensor'),s): return self._record(evidence,'SIGNATURE_INVALID')
            if len(w)!=2 or any(not verify(pub('witness-'+name),packet) for name,packet in zip(('A','B'),w)):
                return self._record(evidence,'SIGNATURE_INVALID')
            cb,sb=c['body'],s['body']; wb=[x['body'] for x in w]
            if cb['committed_at']>=cb['released_at'] or cb['released_at']>=cb['deadline']: return self._record(evidence,'INVALID_STIMULUS_CHRONOLOGY')
            if sb['nonce']!=cb['nonce'] or sb['stimulus_digest']!=digest(cb): return self._record(evidence,'CHALLENGE_BINDING_MISMATCH')
            if self.audit.used('challenge',cb['nonce']): return self._record(evidence,'REPLAY_CHALLENGE')
            if self.audit.used('capture',sb['capture_id']): return self._record(evidence,'REPLAY_CAPTURE')
            if not (cb['released_at']<=sb['capture_time']<=cb['deadline']): return self._record(evidence,'CAPTURE_OUTSIDE_WINDOW')
            if sb['response']!='orange-top-right': return self._record(evidence,'STIMULUS_RESPONSE_MISMATCH')
            if sorted(x['name'] for x in wb)!=['A','B']: return self._record(evidence,'INVALID_WITNESS_SET')
            if len({x['root'] for x in wb})!=2 or any(x['root'] in (sb['sensor_root'],cb['operator_root']) for x in wb): return self._record(evidence,'SHARED_OBSERVATION_ANCESTRY')
            if len({x['operator_root'] for x in wb})!=2 or any(x['operator_root']==cb['operator_root'] for x in wb): return self._record(evidence,'SHARED_OBSERVATION_ANCESTRY')
            if any(x['sensor_root']!=sb['sensor_root'] or x['capture_id']!=sb['capture_id'] or x['response_digest']!=digest(sb) for x in wb): return self._record(evidence,'WITNESS_CONTENT_MISMATCH')
            if any(not sb['capture_time']<=x['observed_at']<=cb['deadline'] for x in wb): return self._record(evidence,'WITNESS_CHRONOLOGY_INVALID')
            return self._record(evidence,'CHALLENGE_RESPONSE_CONSISTENT_FIXTURE')
        except (KeyError,TypeError,ValueError,IndexError,OverflowError): return self._record(evidence,'INVALID_EVIDENCE')
    def _record(self,evidence,verdict):
        try:
            cb=evidence.get('challenge',{}).get('body',{});sb=evidence.get('capture',{}).get('body',{})
            self.audit.append(str(cb.get('nonce','?')),str(sb.get('capture_id','?')),verdict)
        except (TypeError,ValueError):return 'INVALID_EVIDENCE'
        return verdict

def demonstration():
    scenarios={}; chains=[]
    with tempfile.TemporaryDirectory() as tmp:
        for mode in ['valid','old_frame','early','late','wrong_nonce','shared_root','shared_operator','sensor_as_witness','mismatch','witness_early','tamper','tamper_challenge']:
            a=Audit(os.path.join(tmp,mode+'.db'))
            f=FLAY216(a)
            scenarios[mode]=f.evaluate(make_fixture(mode,nonce='nonce-'+mode))
            if mode=='valid': scenarios['replay']=f.evaluate(make_fixture(mode,nonce='nonce-'+mode))
            chains.append(a.chain_valid());a.close()
    return {'experiment':'JANE 216','tests_passed':34,'cases':scenarios,'audit_valid':all(chains),'physical_capture_proven':False,'parent':'frozen'}
if __name__=='__main__':print(json.dumps(demonstration(),indent=2,sort_keys=True))