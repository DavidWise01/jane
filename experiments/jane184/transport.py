"""JANE 184: authenticated transport of JANE183 compact consistency proof.

The relay signature authenticates a delivered bundle, not real-world custody or time.
"""
import hashlib, json, sqlite3, os, sys
from contextlib import contextmanager
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'..','jane183')))
from compact import leaf, make_proof, signed_checkpoint, signer, verify, enc, h, hash_ok

def sha(x): return hashlib.sha256(enc(x)).hexdigest()

def identity(label):
    key=Ed25519PrivateKey.from_private_bytes(h(('JANE184:'+label).encode()))
    return key,key.public_key()

def pack(proof,old_receipts,new_receipts,relay_key,relay_id,nonce,issued_ms,expires_ms):
    body=dict(schema='jane184.envelope.v1',proof=proof,old_receipts=old_receipts,new_receipts=new_receipts,
              relay=relay_id,nonce=nonce,issued_ms=issued_ms,expires_ms=expires_ms)
    return dict(body=body,relay_signature=relay_key.sign(enc(body)).hex())

class Audit:
    def __init__(self, db_path, custodians, relays, quorum=3, max_bytes=65536, max_lifetime_ms=300000, max_skew_ms=30000):
        self.db_path=str(db_path)
        self.keys={s.name:s for s in custodians}
        self.relays=relays
        self.quorum=quorum
        self.max_bytes=max_bytes
        self.max_lifetime_ms=max_lifetime_ms
        self.max_skew_ms=max_skew_ms
        self.active_parent='frozen_parent'
        with self.conn() as c:
            c.execute('CREATE TABLE IF NOT EXISTS used (relay TEXT NOT NULL, nonce TEXT NOT NULL, PRIMARY KEY(relay,nonce))')
            c.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, code TEXT NOT NULL, digest TEXT NOT NULL, previous TEXT NOT NULL)')
    @contextmanager
    def conn(self):
        db=sqlite3.connect(self.db_path)
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    def record(self,code):
        with self.conn() as c:
            prev=c.execute('SELECT digest FROM events ORDER BY seq DESC LIMIT 1').fetchone()
            previous=prev[0] if prev else '0'*64
            seq=c.execute('SELECT COUNT(*) FROM events').fetchone()[0]
            dig=sha(dict(seq=seq,code=code,previous=previous))
            c.execute('INSERT INTO events VALUES (?,?,?,?)',(seq,code,dig,previous))
    def chain(self):
        with self.conn() as c: entries=c.execute('SELECT seq,code,digest,previous FROM events ORDER BY seq').fetchall()
        prev='0'*64
        for expected,(i,code,digest,previous) in enumerate(entries):
            if previous!=prev or digest!=sha(dict(seq=i,code=code,previous=prev)) or i!=expected:return 'TAMPERED'
            prev=digest
        return 'VALID_LOCAL_CHAIN'
    def check_receipts(self,rs):
        if not isinstance(rs,list) or not rs:return 'BAD_CHECKPOINT',None
        if not all(isinstance(r,dict) for r in rs):return 'BAD_CHECKPOINT',None
        b=rs[0].get('body')
        if not isinstance(b,dict) or b.get('schema')!='jane183.checkpoint.v1' or type(b.get('size')) is not int or not 1<=b['size']<=1024 or not hash_ok(b.get('root')) or type(b.get('epoch')) is not int or not isinstance(b.get('nonce'),str):return 'BAD_CHECKPOINT',None
        admins=set();seen=set()
        for r in rs:
            if r.get('body')!=b:return 'CONFLICTING_CHECKPOINTS',None
            name=r.get('signer')
            if name in seen:return 'DUPLICATE_CUSTODIAN',None
            seen.add(name)
            key=self.keys.get(name)
            if not key:return 'UNKNOWN_CUSTODIAN',None
            try:key.public.verify(bytes.fromhex(r['signature']),enc(b))
            except (InvalidSignature,ValueError,KeyError,TypeError):return 'BAD_CUSTODY_SIGNATURE',None
            admins.add(key.administrator)
        if len(admins)<self.quorum:return 'INSUFFICIENT_DECLARED_ROOTS',None
        return 'OK',b
    def receive(self,packet,now_ms):
        def decision():
            if type(now_ms) is not int:return 'BAD_LOCAL_TIME'
            if not isinstance(packet,dict) or not isinstance(packet.get('body'),dict) or not isinstance(packet.get('relay_signature'),str):return 'MALFORMED'
            try: size=len(enc(packet))
            except (TypeError,ValueError,OverflowError):return 'MALFORMED'
            if size>self.max_bytes:return 'OVERSIZED'
            b=packet['body']
            if b.get('schema')!='jane184.envelope.v1':return 'BAD_SCHEMA'
            relay=b.get('relay');nonce=b.get('nonce');start=b.get('issued_ms');end=b.get('expires_ms')
            if not isinstance(relay,str) or relay not in self.relays:return 'UNKNOWN_RELAY'
            if not isinstance(nonce,str) or not 1<=len(nonce)<=128:return 'BAD_NONCE'
            if type(start) is not int or type(end) is not int or not start<end or end-start>self.max_lifetime_ms:return 'BAD_LIFETIME'
            try:self.relays[relay].verify(bytes.fromhex(packet['relay_signature']),enc(b))
            except (InvalidSignature,ValueError,TypeError):return 'BAD_RELAY_SIGNATURE'
            if start>now_ms+self.max_skew_ms:return 'FUTURE_ENVELOPE'
            if now_ms>end:return 'EXPIRED_ENVELOPE'
            with self.conn() as c:
                if c.execute('SELECT 1 FROM used WHERE relay=? AND nonce=?',(relay,nonce)).fetchone():return 'REPLAY'
            old_status,old=self.check_receipts(b.get('old_receipts'))
            if old_status!='OK':return old_status
            new_status,new=self.check_receipts(b.get('new_receipts'))
            if new_status!='OK':return new_status
            if new['size']<old['size'] or new['epoch']<=old['epoch']:return 'CHECKPOINT_ROLLBACK'
            p=b.get('proof')
            if not isinstance(p,dict) or p.get('old_size')!=old['size'] or p.get('new_size')!=new['size'] or not verify(p,old['root'],new['root']):return 'INVALID_CONSISTENCY_PROOF'
            # Atomic acceptance and persistent nonce: no local clock claims beyond supplied now_ms.
            with self.conn() as c:
                try:c.execute('INSERT INTO used(relay,nonce) VALUES (?,?)',(relay,nonce))
                except sqlite3.IntegrityError:return 'REPLAY'
            return 'AUTHENTICATED_DELIVERY_FIXTURE'
        outcome=decision()
        self.record(outcome)
        return outcome

def fixture(tmp=':memory:'):
    witnesses=[signer('root'+str(i),'admin'+str(i)) for i in range(3)]
    relay_private,relay_public=identity('relayA')
    xs=[leaf(dict(sequence=i,value=i*i)) for i in range(1,10)]
    old=signed_checkpoint(xs[:6],witnesses,6,'checkpoint-six')
    new=signed_checkpoint(xs,witnesses,9,'checkpoint-nine')
    p=make_proof(xs,6)
    packet=pack(p,old,new,relay_private,'relayA','delivery-001',1000,2000)
    return Audit(tmp,witnesses,{'relayA':relay_public}),packet,relay_private

def demo():
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        path=os.path.join(folder,'audit.sqlite')
        audit,packet,_=fixture(path)
        first=audit.receive(packet,1500)
        replay=audit.receive(packet,1500)
        restarted,_,_=fixture(path)
        after_restart=restarted.receive(packet,1500)
        return dict(experiment='JANE-184',status=first,replay=replay,restart_replay=after_restart,
                    chain=restarted.chain(),old_size=6,new_size=9,
                    original_checkpoint_signatures=3,relay_signature_verified=True,
                    independent_custodians_verified=False,active_parent_changed=False)
if __name__=='__main__':print(json.dumps(demo(),indent=2))