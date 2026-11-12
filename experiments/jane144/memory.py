"""JANE 144 compact signed SQLite witness memory.
Exact tested implementation and 24 tests: jane144-tested.zip.
This reproduction uses fixture identities/keys and a local retained anchor.
"""
from datetime import datetime,timezone,timedelta
from hashlib import sha256
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
import sqlite3,json
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def digest(x):return sha256(enc(x)).hexdigest()
class Memory:
 def __init__(self,path,anchor):
  self.db=sqlite3.connect(path)
  self.anchor=Path(anchor)
  self.db.executescript("CREATE TABLE IF NOT EXISTS keys(id TEXT PRIMARY KEY,pub BLOB,root TEXT,gen INT,active INT);CREATE TABLE IF NOT EXISTS nonce(root TEXT,n TEXT,PRIMARY KEY(root,n));CREATE TABLE IF NOT EXISTS claims(root TEXT,case_id TEXT,seq INT,value INT,digest TEXT,PRIMARY KEY(root,case_id,seq,digest));CREATE TABLE IF NOT EXISTS events(seq INT PRIMARY KEY,kind TEXT,body TEXT,prev TEXT,head TEXT);")
 def event(self,kind,body):
  row=self.db.execute("SELECT seq,head FROM events ORDER BY seq DESC LIMIT 1").fetchone()
  seq=row[0]+1 if row else 0;prev=row[1] if row else '0'*64
  h=digest(dict(seq=seq,kind=kind,body=body,prev=prev))
  self.db.execute("INSERT INTO events VALUES(?,?,?,?,?)",(seq,kind,json.dumps(body,sort_keys=True),prev,h))
 def genesis(self,id,pub,root):
  if len(pub)!=32 or not root or self.db.execute("SELECT 1 FROM keys WHERE root=?",(root,)).fetchone():raise ValueError("genesis")
  with self.db:
   self.db.execute("INSERT INTO keys VALUES(?,?,?,?,1)",(id,pub,root,0))
   self.event("GENESIS",dict(id=id,root=root,pub=digest(list(pub))))
 def rotate(self,old,new,pub,chronos,signature):
  row=self.db.execute("SELECT pub,root,gen,active FROM keys WHERE id=?",(old,)).fetchone()
  if not row or not row[3] or len(pub)!=32 or self.db.execute("SELECT 1 FROM keys WHERE id=?",(new,)).fetchone():raise ValueError("rotation")
  p=dict(domain="JANE-144-ROTATE",old=old,new=new,pub=digest(list(pub)),root=row[1],gen=row[2]+1,chronos=chronos)
  try:Ed25519PublicKey.from_public_bytes(row[0]).verify(signature,enc(p))
  except (InvalidSignature,ValueError):raise ValueError("signature") from None
  with self.db:
   self.db.execute("UPDATE keys SET active=0 WHERE id=?",(old,))
   self.db.execute("INSERT INTO keys VALUES(?,?,?,?,1)",(new,pub,row[1],row[2]+1))
   self.event("ROTATE",p)
 def ingest(self,p,signature):
  if set(p)!=set(("domain","key_id","nonce","case_id","sequence","value","chronos")) or p["domain"]!="JANE-144-OUTCOME":return "BAD_SCHEMA"
  row=self.db.execute("SELECT pub,root,active FROM keys WHERE id=?",(p["key_id"],)).fetchone()
  if not row or not row[2]:return "UNKNOWN_OR_RETIRED"
  try:Ed25519PublicKey.from_public_bytes(row[0]).verify(signature,enc(p))
  except (InvalidSignature,ValueError,TypeError):return "BAD_SIGNATURE"
  if type(p["value"]) is not bool or type(p["sequence"]) is not int or p["sequence"]<0 or not isinstance(p["nonce"],str) or len(p["nonce"])<12:return "BAD_CLAIM"
  with self.db:
   if self.db.execute("SELECT 1 FROM nonce WHERE root=? AND n=?",(row[1],p["nonce"])).fetchone():return "REPLAY"
   self.db.execute("INSERT INTO nonce VALUES(?,?)",(row[1],p["nonce"]))
   self.db.execute("INSERT INTO claims VALUES(?,?,?,?,?)",(row[1],p["case_id"],p["sequence"],int(p["value"]),digest(p)))
   self.event("ACCEPT",dict(root=row[1],claim=digest(p)))
  return "ACCEPTED"
 def decide(self,case,seq,required=3):
  rows=self.db.execute("SELECT root,value FROM claims WHERE case_id=? AND seq=?",(case,seq)).fetchall()
  byroot={}
  for root,val in rows:byroot.setdefault(root,set()).add(val)
  if any(len(vals)>1 for vals in byroot.values()):return "EQUIVOCATION"
  if len({next(iter(vals)) for vals in byroot.values()})>1:return "CONFLICT"
  return "RESOLVED" if len(byroot)>=required else "UNRESOLVED"
 def head(self):
  x=self.db.execute("SELECT head FROM events ORDER BY seq DESC LIMIT 1").fetchone()
  return x[0] if x else '0'*64
 def export_anchor(self):
  self.anchor.write_text(json.dumps(dict(head=self.head(),count=self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0])))
 def audit(self):
  prev='0'*64
  for i,(seq,kind,body,prior,head) in enumerate(self.db.execute("SELECT * FROM events ORDER BY seq")):
   if seq!=i or prior!=prev or head!=digest(dict(seq=seq,kind=kind,body=json.loads(body),prev=prev)):return "TAMPERED"
   prev=head
  if self.anchor.exists():
   a=json.loads(self.anchor.read_text())
   if a["head"]!=prev or a["count"]!=self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]:return "ROLLBACK_OR_FORK"
   return "ANCHORED_MATCH"
  return "VALID_LOCAL_ONLY"
