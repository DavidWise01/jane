import unittest,tempfile
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from memory import Memory,enc,digest
def pub(k):return k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name);self.m=Memory(self.p/'m.db',self.p/'head.json')
  self.ks=[Ed25519PrivateKey.generate() for _ in range(3)]
  for i,k in enumerate(self.ks):self.m.genesis('k'+str(i),pub(k),'root'+str(i))
 def tearDown(self):self.m.db.close();self.t.cleanup()
 def receipt(self,i,value=True,nonce=None):
  p=dict(domain='JANE-144-OUTCOME',key_id='k'+str(i),nonce=nonce or 'long-nonce-'+str(i)+'-testing',case_id='C0',sequence=7,value=value,chronos='{{ 2026.11.12 }}')
  return p,self.ks[i].sign(enc(p))
 def test_three(self):
  for i in range(3):self.assertEqual(self.m.ingest(*self.receipt(i)),'ACCEPTED')
  self.assertEqual(self.m.decide('C0',7),'RESOLVED')
 def test_replay(self):
  r=self.receipt(0);self.m.ingest(*r);self.assertEqual(self.m.ingest(*r),'REPLAY')
 def test_restart(self):
  r=self.receipt(0);self.m.ingest(*r);self.m.db.close();self.m=Memory(self.p/'m.db',self.p/'head.json')
  self.assertEqual(self.m.ingest(*r),'REPLAY')
 def test_equivocation(self):
  self.m.ingest(*self.receipt(0));self.m.ingest(*self.receipt(0,False,'another-long-nonce'))
  self.assertEqual(self.m.decide('C0',7),'EQUIVOCATION')
 def test_fork(self):
  self.m.ingest(*self.receipt(0));self.m.ingest(*self.receipt(1,False))
  self.assertEqual(self.m.decide('C0',7),'CONFLICT')
 def test_anchor(self):self.m.export_anchor();self.assertEqual(self.m.audit(),'ANCHORED_MATCH')
 def test_recovery(self):
  self.m.export_anchor();self.m.ingest(*self.receipt(0));self.assertEqual(self.m.audit(),'ROLLBACK_OR_FORK')
 def test_forced_signature(self):
  p,s=self.receipt(0);p=dict(p,value=False);self.assertEqual(self.m.ingest(p,s),'BAD_SIGNATURE')
if __name__=='__main__':unittest.main(verbosity=2)
