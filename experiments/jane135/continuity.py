"""JANE 135 compact persistent witness continuity. Offline prototype."""
import sqlite3,json,hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def hashit(v):return hashlib.sha256(canonical(v)).hexdigest()
class WitnessLedger:
 def __init__(self,path):
  self.db=sqlite3.connect(path)
  self.db.execute("CREATE TABLE IF NOT EXISTS keys(id TEXT PRIMARY KEY,pub BLOB,custody TEXT,generation INT,active INT)")
  self.db.execute("CREATE TABLE IF NOT EXISTS nonces(custody TEXT,nonce TEXT,PRIMARY KEY(custody,nonce))")
  self.db.execute("CREATE TABLE IF NOT EXISTS log(seq INTEGER PRIMARY KEY,kind TEXT,body TEXT,prev TEXT,head TEXT)")
  self.db.commit()
 def _event(self,kind,body):
  row=self.db.execute("SELECT seq,head FROM log ORDER BY seq DESC LIMIT 1").fetchone()
  seq=row[0]+1 if row else 0;prev=row[1] if row else '0'*64
  head=hashit(dict(seq=seq,kind=kind,body=body,prev=prev))
  self.db.execute("INSERT INTO log VALUES(?,?,?,?,?)",(seq,kind,canonical(body).decode(),prev,head))
 def genesis(self,id,pub,custody):
  if not id or len(pub)!=32 or not custody or self.db.execute("SELECT 1 FROM keys WHERE custody=?",(custody,)).fetchone():raise ValueError("genesis")
  with self.db:
   self.db.execute("INSERT INTO keys VALUES(?,?,?,?,1)",(id,pub,custody,0))
   self._event("GENESIS",dict(id=id,custody=custody,public_hash=hashlib.sha256(pub).hexdigest()))
 def rotate(self,old,new,pub,chronos,signature):
  row=self.db.execute("SELECT pub,custody,generation,active FROM keys WHERE id=?",(old,)).fetchone()
  if not row or not row[3] or len(pub)!=32 or self.db.execute("SELECT 1 FROM keys WHERE id=?",(new,)).fetchone():raise ValueError("rotation")
  body=dict(domain="JANE-135-ROTATE",old_id=old,new_id=new,new_public_sha256=hashlib.sha256(pub).hexdigest(),custody=row[1],generation=row[2]+1,chronos=chronos)
  try:Ed25519PublicKey.from_public_bytes(row[0]).verify(signature,canonical(body))
  except (InvalidSignature,ValueError):raise ValueError("signature") from None
  with self.db:
   self.db.execute("UPDATE keys SET active=0 WHERE id=?",(old,))
   self.db.execute("INSERT INTO keys VALUES(?,?,?,?,1)",(new,pub,row[1],row[2]+1))
   self._event("ROTATE",body)
 def receipt(self,id,nonce,claim_hash,chronos,signature):
  row=self.db.execute("SELECT pub,custody,active FROM keys WHERE id=?",(id,)).fetchone()
  if not row or not row[2] or len(nonce)<12:return "REJECTED"
  body=dict(domain="JANE-135-RECEIPT",key_id=id,nonce=nonce,claim_hash=claim_hash,chronos=chronos)
  try:Ed25519PublicKey.from_public_bytes(row[0]).verify(signature,canonical(body))
  except (InvalidSignature,ValueError):return "BAD_SIGNATURE"
  try:
   with self.db:
    self.db.execute("INSERT INTO nonces VALUES(?,?)",(row[1],nonce))
    self._event("RECEIPT",dict(custody=row[1],nonce=nonce,payload_hash=hashit(body)))
  except sqlite3.IntegrityError:return "REPLAY"
  return "ACCEPTED"
 def audit(self,expected_head=None):
  prev='0'*64
  for i,(seq,kind,body,prior,head) in enumerate(self.db.execute("SELECT seq,kind,body,prev,head FROM log ORDER BY seq")):
   if seq!=i or prior!=prev or hashit(dict(seq=seq,kind=kind,body=json.loads(body),prev=prior))!=head:return "CHAIN_TAMPERED"
   prev=head
  return "EXTERNAL_HEAD_MISMATCH" if expected_head is not None and expected_head!=prev else "VALID"
