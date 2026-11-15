"""JANE 214: challenge-bound sensor acquisition, fixture-only evidence."""
from __future__ import annotations
import hashlib, json, sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def sha(x): return hashlib.sha256(canonical(x)).hexdigest()
def sign(body,key): return {'body':body,'signature':key.sign(canonical(body)).hex()}
def verify(packet,key):
    try:
        key.verify(bytes.fromhex(packet['signature']),canonical(packet['body']))
        return True
    except (InvalidSignature,ValueError,TypeError,KeyError,AttributeError): return False

def hex64(s): return isinstance(s,str) and len(s)==64 and all(c in '0123456789abcdef' for c in s)
@dataclass(frozen=True)
class Policy:
    min_roots:int=2
    min_sensors:int=2
    max_delay:int=40

class Ledger:
    def __init__(self,path=':memory:'):
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS used (challenge TEXT PRIMARY KEY, evidence TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS captures (capture TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY, prev TEXT NOT NULL, head TEXT NOT NULL, event TEXT NOT NULL)')
        self.db.commit()
    def close(self): self.db.close()
    def seen(self,c): return self.db.execute('SELECT 1 FROM used WHERE challenge=?',(c,)).fetchone() is not None
    def captured(self,c): return self.db.execute('SELECT 1 FROM captures WHERE capture=?',(c,)).fetchone() is not None
    def healthy(self):
        prev='0'*64
        for seq,old,head,event in self.db.execute('SELECT seq,prev,head,event FROM audit ORDER BY seq'):
            if old!=prev or head!=sha([seq,old,json.loads(event)]): return False
            prev=head
        return True
    def record(self,challenge,evidence,captures):
        row=self.db.execute('SELECT seq,head FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
        seq=(row[0]+1) if row else 1;prev=row[1] if row else '0'*64
        event={'challenge':challenge,'evidence':evidence,'captures':sorted(captures)}
        with self.db:
            self.db.execute('INSERT INTO used VALUES (?,?)',(challenge,evidence))
            for ident,payload in captures.items():self.db.execute('INSERT INTO captures VALUES (?,?)',(ident,payload))
            self.db.execute('INSERT INTO audit VALUES (?,?,?,?)',(seq,prev,sha([seq,prev,event]),canonical(event).decode()))

class FLAY214:
    def __init__(self,keys,ledger,policy=Policy()): self.keys=keys;self.ledger=ledger;self.policy=policy
    def inspect(self,packet):
        if not self.ledger.healthy():return {'verdict':'CORRUPT_AUDIT'}
        try:
            challenge=packet['challenge']; observations=packet['observations']; cb=challenge['body']; nonce=cb['nonce']
            if not isinstance(nonce,str) or len(nonce)<24:return {'verdict':'INVALID_NONCE'}
            if self.ledger.seen(nonce):return {'verdict':'REPLAY_CHALLENGE'}
            if not isinstance(observations,list) or not observations:return {'verdict':'MISSING_OBSERVATIONS'}
            for p in [challenge,*observations]:
                b=p['body'];ident=b['id']
                if ident not in self.keys or not verify(p,self.keys[ident]):return {'verdict':'SIGNATURE_INVALID'}
            tick=cb['issued']; expires=cb['expires']; task=cb['task']
            if any(type(x)!=int for x in (tick,expires)) or tick<0 or expires<=tick:return {'verdict':'INVALID_CHRONOLOGY'}
            if not isinstance(task,str) or not hex64(task):return {'verdict':'INVALID_TASK'}
            if len({p['body']['id'] for p in [challenge,*observations]})!=len(observations)+1:return {'verdict':'DUPLICATE_SIGNER'}
            roots=set();sensors=set();captures={};payloads=set()
            for obs in observations:
                b=obs['body'];c=b['capture_id'];sensor=b['sensor'];root=b['root']
                if not all(isinstance(x,str) and x for x in (c,sensor,root)) or len(c)<8:return {'verdict':'MISSING_PROVENANCE'}
                if b.get('nonce')!=nonce or b.get('task')!=task:return {'verdict':'CHALLENGE_MISMATCH'}
                start=b['start'];end=b['end']
                if type(start)!=int or type(end)!=int or start<tick or end<start or end>expires or end-tick>self.policy.max_delay:return {'verdict':'INVALID_CAPTURE_CHRONOLOGY'}
                if not hex64(b.get('payload_hash')):return {'verdict':'INVALID_PAYLOAD_HASH'}
                if c in captures or self.ledger.captured(c):return {'verdict':'REPLAY_CAPTURE'}
                captures[c]=b['payload_hash'];payloads.add(b['payload_hash']);roots.add(root);sensors.add(sensor)
                if b.get('sensor_boot') is None or not isinstance(b['sensor_boot'],str) or not b['sensor_boot']:return {'verdict':'MISSING_BOOT_PROVENANCE'}
                if not isinstance(b.get('frame'),int) or isinstance(b['frame'],bool) or b['frame']<0:return {'verdict':'INVALID_FRAME'}
            if len(roots)<self.policy.min_roots:return {'verdict':'SHARED_ANCESTRY'}
            if len(sensors)<self.policy.min_sensors:return {'verdict':'SHARED_SENSOR'}
            if len(payloads)!=1:return {'verdict':'EFFECT_DISAGREEMENT'}
            self.ledger.record(nonce,sha(packet),captures)
            return {'verdict':'FRESH_ACQUISITION_FIXTURE','roots':len(roots),'sensors':len(sensors),'evidence_hash':sha(packet)}
        except (KeyError,TypeError,ValueError,AttributeError,sqlite3.IntegrityError):return {'verdict':'MALFORMED_EVIDENCE'}

def fixture():
    keys={k:Ed25519PrivateKey.from_private_bytes(bytes([i])*32) for i,k in enumerate(['scheduler','scope-a','scope-b'],1)}
    task=sha({'task':'read fresh frame'}); nonce='a'*32;payload=sha({'frame':'new','data':[1,2,3]})
    challenge=sign({'id':'scheduler','nonce':nonce,'task':task,'issued':100,'expires':160},keys['scheduler'])
    obs=[]
    for idx,ident in enumerate(['scope-a','scope-b']):
        body={'id':ident,'nonce':nonce,'task':task,'start':110+idx,'end':115+idx,'capture_id':'capture-'+ident+'-001','sensor':'sensor-'+ident,'root':'root-'+ident,'sensor_boot':'boot-'+ident,'frame':7,'payload_hash':payload}
        obs.append(sign(body,keys[ident]))
    return {'challenge':challenge,'observations':obs},{k:v.public_key() for k,v in keys.items()},keys

if __name__=='__main__':
    import copy
    cases={}
    for name,modifier in [('fresh',lambda x:x),('shared_sensor',lambda x:x['observations'][1]['body'].__setitem__('sensor','sensor-scope-a')),('late_capture',lambda x:x['observations'][0]['body'].__setitem__('end',170)),('shared_root',lambda x:x['observations'][1]['body'].__setitem__('root','root-scope-a'))]:
        p,pubs,priv=fixture();modifier(p)
        for obs in p['observations']:obs['signature']=priv[obs['body']['id']].sign(canonical(obs['body'])).hex()
        ledger=Ledger();cases[name]=FLAY214(pubs,ledger).inspect(p);ledger.close()
    p,pubs,_=fixture();ledger=Ledger();v=FLAY214(pubs,ledger);cases['first']=v.inspect(p);cases['replay']=v.inspect(p);ledger.close()
    print(json.dumps({'experiment':214,'cases':cases,'limitations':['Synthetic keys, sensor metadata, and clocks; signatures cannot prove physical acquisition or independent hardware.']},indent=2))