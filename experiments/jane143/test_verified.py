import unittest
from datetime import timedelta
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from verified import *
class Tests(unittest.TestCase):
 def setUp(self):
  self.ks={i:Ed25519PrivateKey.generate() for i in range(3)}
  self.keys={str(i):Key(k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw),str(i)) for i,k in self.ks.items()}
  self.anchors={str(i):'a'*64 for i in range(3)}
  self.f=FLAY([Case("C0",None,True,False,50)],self.keys,self.anchors,chronos(STAMP,-360))
 def r(self,i=0,value=False):
  p=dict(key_id=str(i),case_id="C0",case_digest=self.f.cases["C0"].binding(),truth=value,nonce=f'nonce-{i}-unique-xxx',chronos=STAMP,offset=-360,anchor='a'*64)
  return Receipt(p,self.ks[i].sign(enc(p)))
 def test_accept(self):self.assertEqual(self.f.ingest(self.r()),"ACCEPTED")
 def test_partial(self):self.f.ingest(self.r());self.assertEqual(self.f.resolve("C0")[0],"UNKNOWN")
 def test_quorum(self):
  for i in range(3):self.f.ingest(self.r(i))
  self.assertEqual(self.f.resolve("C0"),("RESOLVED",False))
 def test_conflict(self):
  self.f.ingest(self.r(0,False));self.f.ingest(self.r(1,True))
  self.assertEqual(self.f.evaluate()["status"],"QUARANTINE_CONFLICT")
 def test_replay(self):
  r=self.r();self.f.ingest(r);self.assertEqual(self.f.ingest(r),"REPLAY")
 def test_tamper(self):
  r=self.r();p=dict(r.claim,truth=True)
  self.assertEqual(self.f.ingest(Receipt(p,r.signature)),"SIGNATURE")
 def test_stale(self):
  self.f.now+=timedelta(hours=1)
  self.assertEqual(self.f.ingest(self.r()),"STALE")
 def test_no_learning(self):self.assertFalse(self.f.evaluate()["learning_applied"])
 def test_active(self):self.assertEqual(self.f.active,"frozen_parent")
 def test_hold_unknown(self):self.assertEqual(self.f.evaluate()["status"],"HOLD_UNCERTAIN_RISK")
 def test_hash_events(self):self.assertEqual(len(self.f.events[-1]["head"]),64)
 def test_chronos(self):self.assertEqual(chronos(STAMP,-360).hour,17)
if __name__=="__main__":unittest.main(verbosity=2)
