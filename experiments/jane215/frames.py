"""JANE 215: content-aware sensor replay audit. Synthetic evidence only.

Canonical pixels are RGB bytes in row-major order. Encoding metadata is excluded
from the fingerprint. Equal frames are a suspicion, not proof of replay.
"""
import hashlib, json, sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def digest(x):return hashlib.sha256(enc(x)).hexdigest()
def signed(body,key):return {'body':body,'signature':key.sign(enc(body)).hex()}
def verify(p,pub):
    try:
        pub.verify(bytes.fromhex(p['signature']),enc(p['body']))
        return True
    except (ValueError,InvalidSignature,KeyError,TypeError,AttributeError):return False

def pixels_hash(width,height,pixels):
    if type(width)!=int or type(height)!=int or not (1<=width<=256 and 1<=height<=256):raise ValueError('dimensions')
    if not isinstance(pixels,list) or len(pixels)!=width*height*3 or any(type(v)!=int or not 0<=v<=255 for v in pixels):raise ValueError('RGB8 pixel length/value')
    return hashlib.sha256(b'J215-RGB8\0'+width.to_bytes(2,'big')+height.to_bytes(2,'big')+bytes(pixels)).hexdigest()

@dataclass(frozen=True)
class Policy:
    max_age:int=30
    min_roots:int=2
    min_sensors:int=2

class Ledger:
    def __init__(self,path=':memory:'):
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS challenge (nonce TEXT PRIMARY KEY,head TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS sensor (id TEXT PRIMARY KEY,seq INTEGER NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS fingerprint (sensor TEXT,fp TEXT,nonce TEXT,PRIMARY KEY(sensor,fp))')
        self.db.execute('CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY,prev TEXT,head TEXT,event TEXT)')
        self.db.commit()
    def close(self):self.db.close()
    def healthy(self):
        prev='0'*64
        for num,old,head,event in self.db.execute('SELECT seq,prev,head,event FROM audit ORDER BY seq'):
            if old!=prev or head!=digest([num,old,json.loads(event)]):return False
            prev=head
        return True
    def seen(self,nonce):return self.db.execute('SELECT 1 FROM challenge WHERE nonce=?',(nonce,)).fetchone() is not None
    def last_seq(self,sensor):
        row=self.db.execute('SELECT seq FROM sensor WHERE id=?',(sensor,)).fetchone();return row[0] if row else None
    def old_fp(self,sensor,fp):return self.db.execute('SELECT nonce FROM fingerprint WHERE sensor=? AND fp=?',(sensor,fp)).fetchone()
    def record(self,nonce,evidence,observations):
        row=self.db.execute('SELECT seq,head FROM audit ORDER BY seq DESC LIMIT 1').fetchone();n=row[0]+1 if row else 1;prev=row[1] if row else '0'*64
        event={'nonce':nonce,'evidence':evidence,'observations':[(o['sensor'],o['seq'],o['fingerprint']) for o in observations]}
        with self.db:
            self.db.execute('INSERT INTO challenge VALUES (?,?)',(nonce,evidence))
            for o in observations:
                self.db.execute('INSERT INTO sensor VALUES (?,?) ON CONFLICT(id) DO UPDATE SET seq=excluded.seq',(o['sensor'],o['seq']))
                self.db.execute('INSERT OR IGNORE INTO fingerprint VALUES (?,?,?)',(o['sensor'],o['fingerprint'],nonce))
            self.db.execute('INSERT INTO audit VALUES (?,?,?,?)',(n,prev,digest([n,prev,event]),enc(event).decode()))

class FLAY215:
    def __init__(self,keys,ledger,policy=Policy()):self.keys=keys;self.ledger=ledger;self.policy=policy
    def inspect(self,packet):
        if not self.ledger.healthy():return {'verdict':'CORRUPT_AUDIT'}
        try:
            challenge=packet['challenge'];obs=packet['observations'];c=challenge['body'];nonce=c['nonce'];issued=c['issued'];expires=c['expires']
            if not isinstance(nonce,str) or len(nonce)<24:return {'verdict':'INVALID_NONCE'}
            if self.ledger.seen(nonce):return {'verdict':'REPLAY_CHALLENGE'}
            if type(issued)!=int or type(expires)!=int or not 0<=issued<expires:return {'verdict':'INVALID_CHRONOLOGY'}
            if not isinstance(obs,list) or len(obs)<self.policy.min_roots:return {'verdict':'INSUFFICIENT_OBSERVATIONS'}
            if c['id'] not in self.keys or not verify(challenge,self.keys[c['id']]):return {'verdict':'SIGNATURE_INVALID'}
            roots=set();sensors=set();clean=[];same=set()
            for p in obs:
                b=p['body'];who=b['id'];root=b['root'];sensor=b['sensor'];seq=b['seq'];tick=b['tick']
                if who not in self.keys or not verify(p,self.keys[who]):return {'verdict':'SIGNATURE_INVALID'}
                if not isinstance(root,str) or not root or not isinstance(sensor,str) or not sensor:return {'verdict':'INVALID_PROVENANCE'}
                if root in roots:return {'verdict':'SHARED_ANCESTRY'}
                if sensor in sensors:return {'verdict':'SHARED_SENSOR'}
                roots.add(root);sensors.add(sensor)
                if b['nonce']!=nonce:return {'verdict':'CHALLENGE_MISMATCH'}
                if type(tick)!=int or not issued<=tick<=expires or tick-issued>self.policy.max_age:return {'verdict':'INVALID_CAPTURE_CHRONOLOGY'}
                if type(seq)!=int or seq<1:return {'verdict':'INVALID_SENSOR_SEQUENCE'}
                prev=self.ledger.last_seq(sensor)
                if prev is not None and seq<=prev:return {'verdict':'REPLAY_SENSOR_SEQUENCE'}
                fp=pixels_hash(b['width'],b['height'],b['pixels'])
                if fp!=b['fingerprint']:return {'verdict':'CONTENT_FINGERPRINT_MISMATCH'}
                if self.ledger.old_fp(sensor,fp):same.add(sensor)
                clean.append({'sensor':sensor,'seq':seq,'fingerprint':fp})
            if len(sensors)<self.policy.min_sensors:return {'verdict':'INSUFFICIENT_SENSORS'}
            if len({v['fingerprint'] for v in clean})!=1:return {'verdict':'CONTENT_DISAGREEMENT'}
            # Consistent, properly signed metadata cannot certify physical capture.
            verdict='REPEATED_CONTENT_SUSPECTED' if same else 'NOVEL_CONTENT_FIXTURE'
            self.ledger.record(nonce,digest(packet),clean)
            return {'verdict':verdict,'repeated_sensors':sorted(same),'fingerprint':clean[0]['fingerprint'],'evidence':digest(packet),'physical_freshness_proven':False}
        except (ValueError,TypeError,KeyError,OverflowError,IndexError,AttributeError):return {'verdict':'MALFORMED_EVIDENCE'}

def fixture(n=1,pixels=None,seq=None,encoding='png'):
    keys={name:Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('jane215-'+name).encode()).digest()) for name in ('issuer','observer-a','observer-b')}
    pub={k:v.public_key() for k,v in keys.items()}
    px=list(pixels if pixels is not None else [11,24,38,77,99,120,201,144,39,44,62,80])
    nonce=f'challenge-{n:024d}'
    cb={'id':'issuer','nonce':nonce,'issued':n*100,'expires':n*100+25}
    observations=[]
    for who,root,sensor in [('observer-a','root-a','sensor-a'),('observer-b','root-b','sensor-b')]:
        b={'id':who,'root':root,'sensor':sensor,'seq':n if seq is None else seq,'tick':n*100+4,'nonce':nonce,'width':2,'height':2,'pixels':list(px),'encoding':encoding,'fingerprint':pixels_hash(2,2,px)}
        observations.append(signed(b,keys[who]))
    return {'challenge':signed(cb,keys['issuer']),'observations':observations},keys,pub

def run_demo():
    l=Ledger();p1,k,pub=fixture(1);v=FLAY215(pub,l)
    first=v.inspect(p1)
    p2,_,_=fixture(2,encoding='jpeg');second=v.inspect(p2)
    p3,_,_=fixture(3,pixels=[12,24,38,77,99,120,201,144,39,44,62,80]);third=v.inspect(p3)
    return {'experiment':'JANE 215','scenarios':{'first':first,'same_pixels_new_encoding':second,'changed_pixels':third},'tests':'run python -W error -m unittest -q test_frames.py','invariant':'Fresh metadata != fresh sensor content'}
if __name__=='__main__':print(json.dumps(run_demo(),indent=2,sort_keys=True))