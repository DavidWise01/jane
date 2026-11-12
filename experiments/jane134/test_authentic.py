import unittest
from dataclasses import replace
from datetime import timedelta
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from authentic import fixture,Verifier,Receipt,sign,quorum,utc_time
class Tests(unittest.TestCase):
 def setUp(self):
  self.registry,self.anchors,self.receipts,self.now=fixture()
  self.v=Verifier(self.registry,self.anchors)
 def test_good(self):self.assertEqual(self.v.verify(self.receipts[0],self.now),'AUTHENTICATED')
 def test_quorum(self):self.assertEqual(quorum(self.receipts,self.v,self.now)['status'],'QUORUM_MATCH')
 def test_replay(self):
  r=self.receipts[0];self.assertEqual(self.v.verify(r,self.now),'AUTHENTICATED');self.assertEqual(self.v.verify(r,self.now),'REPLAY')
 def test_tamper(self):
  r=self.receipts[0];p=dict(r.payload);p['claim_digest']='b'*64
  self.assertEqual(self.v.verify(Receipt(p,r.signature),self.now),'BAD_SIGNATURE')
 def test_chronos_tamper(self):
  r=self.receipts[0];p=dict(r.payload);p['chronos']=p['chronos'].replace('21:11:00','21:12:00')
  self.assertEqual(self.v.verify(Receipt(p,r.signature),self.now),'BAD_SIGNATURE')
 def test_revocation(self):
  keys=dict(self.registry);keys['k0']=replace(keys['k0'],active=False)
  self.assertEqual(Verifier(keys,self.anchors).verify(self.receipts[0],self.now),'UNKNOWN_OR_REVOKED_KEY')
 def test_stale(self):self.assertEqual(self.v.verify(self.receipts[0],self.now+timedelta(hours=1)),'STALE_CHRONOS')
 def test_anchor(self):self.assertEqual(Verifier(self.registry,{}).verify(self.receipts[0],self.now),'ANCHOR_MISMATCH')
 def test_shared_custody(self):
  keys=dict(self.registry);keys['k1']=replace(keys['k1'],custody_root='owned:canonical')
  self.assertEqual(quorum(self.receipts,Verifier(keys,self.anchors),self.now)['status'],'QUORUM_INSUFFICIENT')
 def test_no_learning(self):self.assertFalse(quorum(self.receipts,self.v,self.now)['learning_applied'])
 def test_invalid_date(self):
  with self.assertRaises(ValueError):utc_time('{{ - 2026:02:30 || 21:11:00 || +123.45.56 || }}',-360)
 def test_unknown_key(self):
  r=self.receipts[0];p=dict(r.payload);p['key_id']='missing'
  self.assertEqual(self.v.verify(Receipt(p,r.signature),self.now),'UNKNOWN_OR_REVOKED_KEY')
if __name__=='__main__':unittest.main(verbosity=2)
