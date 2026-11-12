import unittest,tempfile,hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from continuity import WitnessLedger,canonical
T='{{ - 2026:11:11 || 22:12:00 || +123.45.56 || }}'
def pub(k):return k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
class Tests(unittest.TestCase):
 def setUp(self):
  self.f=tempfile.NamedTemporaryFile(suffix='.sqlite')
  self.db=WitnessLedger(self.f.name);self.k=Ed25519PrivateKey.generate();self.j=Ed25519PrivateKey.generate();self.db.genesis('g0',pub(self.k),'owned')
 def tearDown(self):self.db.db.close();self.f.close()
 def rotate(self):
  v=dict(domain='JANE-135-ROTATE',old_id='g0',new_id='g1',new_public_sha256=hashlib.sha256(pub(self.j)).hexdigest(),custody='owned',generation=1,chronos=T)
  self.db.rotate('g0','g1',pub(self.j),T,self.k.sign(canonical(v)))
 def receipt(self,id,k):
  v=dict(domain='JANE-135-RECEIPT',key_id=id,nonce='nonce-00000001',claim_hash='a'*64,chronos=T)
  return self.db.receipt(id,v['nonce'],v['claim_hash'],T,k.sign(canonical(v)))
 def test_rotate(self):self.rotate();self.assertEqual(self.db.audit(),'VALID')
 def test_retire(self):self.rotate();self.assertEqual(self.receipt('g0',self.k),'REJECTED')
 def test_new_key(self):self.rotate();self.assertEqual(self.receipt('g1',self.j),'ACCEPTED')
 def test_replay(self):self.receipt('g0',self.k);self.assertEqual(self.receipt('g0',self.k),'REPLAY')
 def test_restart(self):
  self.receipt('g0',self.k);self.db.db.close();self.db=WitnessLedger(self.f.name)
  self.assertEqual(self.receipt('g0',self.k),'REPLAY')
 def test_cross_generation_nonce(self):
  self.receipt('g0',self.k);self.rotate();self.assertEqual(self.receipt('g1',self.j),'REPLAY')
 def test_tamper(self):
  self.db.db.execute("UPDATE log SET kind='BAD' WHERE seq=0");self.db.db.commit()
  self.assertEqual(self.db.audit(),'CHAIN_TAMPERED')
 def test_anchor(self):self.assertEqual(self.db.audit('f'*64),'EXTERNAL_HEAD_MISMATCH')
if __name__=='__main__':unittest.main(verbosity=2)
