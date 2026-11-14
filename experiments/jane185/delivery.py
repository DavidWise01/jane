"""JANE 185: authenticated outbox versus receiver acknowledgment audit.

Synthetic signers; signing alone does not establish independently operated custody.
"""
import hashlib, json, sqlite3
from contextlib import contextmanager
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature


def enc(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
def sha(v): return hashlib.sha256(enc(v)).hexdigest()
def key(label): return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('jane185:'+label).encode()).digest())
def sign(body, private, who): return {'body':body,'signer':who,'signature':private.sign(enc(body)).hex()}
def verify(item, keys):
    try:
        if not isinstance(item,dict) or not isinstance(item['body'],dict): return False
        public=keys.get(item['signer'])
        if public is None:return False
        public.verify(bytes.fromhex(item['signature']),enc(item['body']))
        return True
    except (KeyError,TypeError,ValueError,InvalidSignature,AttributeError):return False

def manifest(message_payloads, epoch=1, nonce='outbox-001', issued_ms=1000):
    if not message_payloads or len(message_payloads)>128:raise ValueError('bounded outbox required')
    entries=[{'seq':i+1,'payload_hash':hashlib.sha256(p).hexdigest()} for i,p in enumerate(message_payloads)]
    return {'schema':'jane185.outbox.v1','epoch':epoch,'nonce':nonce,'issued_ms':issued_ms,'size':len(entries),'entries':entries,'root':sha(entries)}

def ack(seq, payload_hash, nonce, received_ms):
    return {'schema':'jane185.ack.v1','seq':seq,'payload_hash':payload_hash,'nonce':nonce,'received_ms':received_ms}

class FLAY:
    def __init__(self, db_path, sender_key, receiver_key, deadline_ms=300, max_gap=128):
        self.db_path=str(db_path);self.keys={'sender':sender_key,'receiver':receiver_key}
        self.deadline_ms=deadline_ms;self.max_gap=max_gap;self.active_parent='frozen_parent'
        with self.db() as c:
            c.execute('CREATE TABLE IF NOT EXISTS used(kind TEXT, signer TEXT, nonce TEXT, PRIMARY KEY(kind,signer,nonce))')
            c.execute('CREATE TABLE IF NOT EXISTS observations(id INTEGER PRIMARY KEY, code TEXT, prev TEXT, digest TEXT)')
            c.execute('CREATE TABLE IF NOT EXISTS accepted(seq INTEGER PRIMARY KEY,payload_hash TEXT,ack_nonce TEXT)')
            c.execute('CREATE TABLE IF NOT EXISTS manifests(epoch INTEGER PRIMARY KEY,root TEXT,size INTEGER,nonce TEXT)')
    @contextmanager
    def db(self):
        c=sqlite3.connect(self.db_path)
        try:
            yield c;c.commit()
        except Exception:
            c.rollback();raise
        finally:c.close()
    def log(self, code):
        with self.db() as c:
            r=c.execute('SELECT id,digest FROM observations ORDER BY id DESC LIMIT 1').fetchone()
            n=r[0]+1 if r else 0;prev=r[1] if r else '0'*64
            c.execute('INSERT INTO observations VALUES(?,?,?,?)',(n,code,prev,sha([n,code,prev])))
    def audit(self):
        with self.db() as c:r=c.execute('SELECT id,code,prev,digest FROM observations ORDER BY id').fetchall()
        prev='0'*64
        for i,(id,code,p,h) in enumerate(r):
            if id!=i or p!=prev or h!=sha([id,code,p]):return 'TAMPERED'
            prev=h
        return 'VALID_LOCAL_CHAIN'
    def receive(self, signed_manifest, signed_acks, now_ms):
        if not verify(signed_manifest,self.keys) or signed_manifest['signer']!='sender':
            self.log('BAD_SENDER_SIGNATURE');return {'status':'BAD_SENDER_SIGNATURE'}
        m=signed_manifest['body']
        if m.get('schema')!='jane185.outbox.v1' or type(m.get('size')) is not int or not 1<=m['size']<=self.max_gap or not isinstance(m.get('entries'),list) or len(m['entries'])!=m['size'] or sha(m['entries'])!=m.get('root') or type(m.get('issued_ms')) is not int or type(m.get('epoch')) is not int or not isinstance(m.get('nonce'),str):
            self.log('BAD_MANIFEST');return {'status':'BAD_MANIFEST'}
        for i,e in enumerate(m['entries']):
            if not isinstance(e,dict) or e.get('seq')!=i+1 or not isinstance(e.get('payload_hash'),str) or len(e['payload_hash'])!=64 or any(x not in '0123456789abcdef' for x in e['payload_hash']):
                self.log('BAD_MANIFEST');return {'status':'BAD_MANIFEST'}
        if type(now_ms) is not int or now_ms<m['issued_ms']:
            self.log('BAD_CHRONOS');return {'status':'BAD_CHRONOS'}
        if not isinstance(signed_acks,list) or len(signed_acks)>self.max_gap:
            self.log('BAD_ACK_SET');return {'status':'BAD_ACK_SET'}
        known={e['seq']:e['payload_hash'] for e in m['entries']};found={};nonces=set()
        for item in signed_acks:
            if not verify(item,self.keys) or item.get('signer')!='receiver':
                self.log('BAD_RECEIVER_SIGNATURE');return {'status':'BAD_RECEIVER_SIGNATURE'}
            a=item['body']
            if a.get('schema')!='jane185.ack.v1' or type(a.get('seq')) is not int or type(a.get('received_ms')) is not int or not isinstance(a.get('nonce'),str) or a['received_ms']<m['issued_ms'] or a['received_ms']>now_ms:
                self.log('BAD_ACK');return {'status':'BAD_ACK'}
            if a['seq'] not in known:
                self.log('UNEXPECTED_ACK');return {'status':'UNEXPECTED_ACK'}
            if a.get('payload_hash')!=known[a['seq']]:
                self.log('ACK_PAYLOAD_CONFLICT');return {'status':'ACK_PAYLOAD_CONFLICT'}
            if a['seq'] in found:
                if found[a['seq']]!=a:self.log('CONFLICTING_ACK');return {'status':'CONFLICTING_ACK'}
                self.log('DUPLICATE_ACK');return {'status':'DUPLICATE_ACK'}
            if a['nonce'] in nonces:
                self.log('DUPLICATE_NONCE');return {'status':'DUPLICATE_NONCE'}
            nonces.add(a['nonce']);found[a['seq']]=a
        with self.db() as c:
            prior=c.execute('SELECT root,size,nonce FROM manifests WHERE epoch=?',(m['epoch'],)).fetchone()
            if prior and prior!=(m['root'],m['size'],m['nonce']):
                self.log('SIGNED_OUTBOX_FORK');return {'status':'SIGNED_OUTBOX_FORK'}
            if c.execute('SELECT 1 FROM used WHERE kind=? AND signer=? AND nonce=?',('outbox','sender',m['nonce'])).fetchone():
                self.log('REPLAY');return {'status':'REPLAY'}
            for a in found.values():
                if c.execute('SELECT 1 FROM used WHERE kind=? AND signer=? AND nonce=?',('ack','receiver',a['nonce'])).fetchone():
                    self.log('REPLAY');return {'status':'REPLAY'}
            for seq,a in found.items():
                old=c.execute('SELECT payload_hash FROM accepted WHERE seq=?',(seq,)).fetchone()
                if old and old[0]!=a['payload_hash']:
                    self.log('ACK_FORK');return {'status':'ACK_FORK'}
            c.execute('INSERT OR IGNORE INTO manifests VALUES(?,?,?,?)',(m['epoch'],m['root'],m['size'],m['nonce']))
            c.execute('INSERT INTO used VALUES(?,?,?)',('outbox','sender',m['nonce']))
            for seq,a in found.items():
                c.execute('INSERT INTO used VALUES(?,?,?)',('ack','receiver',a['nonce']))
                c.execute('INSERT OR IGNORE INTO accepted VALUES(?,?,?)',(seq,a['payload_hash'],a['nonce']))
        missing=[i for i in known if i not in found]
        late=[i for i in missing if now_ms-m['issued_ms']>self.deadline_ms]
        status='SELECTIVE_SUPPRESSION' if late else 'DELIVERY_PENDING' if missing else 'DELIVERY_COMPLETE_FIXTURE'
        self.log(status)
        return {'status':status,'outbox_size':m['size'],'received':sorted(found),'missing':missing,'overdue':late,'outbox_head':m['root'],'active_parent':self.active_parent,'learning_applied':False,'independent_custody_verified':False}

def fixture(db_path=':memory:',now_ms=1500,missing=(2,)):
    # sqlite :memory: does not persist across connections. Use a temporary file instead.
    import tempfile,os
    if db_path==':memory:':
        fd,db_path=tempfile.mkstemp(prefix='jane185_',suffix='.sqlite');os.close(fd)
    s=key('sender');r=key('receiver')
    m=manifest([b'alpha',b'beta',b'gamma'])
    signed=sign(m,s,'sender')
    rec=[sign(ack(e['seq'],e['payload_hash'],'ack-'+str(e['seq']),m['issued_ms']+50),r,'receiver') for e in m['entries'] if e['seq'] not in missing]
    verifier=FLAY(db_path,s.public_key(),r.public_key())
    return verifier,signed,rec,verifier.receive(signed,rec,now_ms)

if __name__=='__main__':
    f,_,_,v=fixture()
    print(json.dumps({'result':v,'audit':f.audit(),'tests':'execute test_delivery.py'},indent=2))