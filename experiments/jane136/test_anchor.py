import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from anchor import *
class Tests(unittest.TestCase):
 def setUp(self):
  e=()
  for x in ("freeze","pass","propose","activate","drift","restore"):e=append(e,x)
  self.e=e;self.keys={};self.receipts=[]
  for i in range(3):
   k=Ed25519PrivateKey.generate()
   pub=k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
   self.keys[str(i)]=Custodian(str(i),pub)
   p=dict(domain="JANE-136",key_id=str(i),nonce=f"nonce-{i}-checkpoint",sequence=5,
          head=e[-1]["head"],chronos="{{ - 2026:11:12 || 07:18:00 || +123.45.56 || }}")
   self.receipts.append(Receipt(p,k.sign(encode(p))))
 def test_intact(self):self.assertEqual(verify(self.e,self.receipts,self.keys)["status"],"ANCHORED_MATCH")
 def test_short_valid(self):self.assertTrue(chain_valid(self.e[:-2]))
 def test_rollback(self):self.assertEqual(verify(self.e[:-2],self.receipts,self.keys)["status"],"ROLLBACK_DETECTED")
 def test_two_roots(self):self.assertEqual(verify(self.e,self.receipts[:2],self.keys)["status"],"INSUFFICIENT_ROOTS")
 def test_tamper(self):
  e=list(self.e);e[0]=dict(e[0],text="forged")
  self.assertEqual(verify(e,self.receipts,self.keys)["status"],"CHAIN_TAMPERED")
 def test_bad_signature(self):
  r=self.receipts[0];p=dict(r.payload,head="b"*64)
  receipts=[Receipt(p,r.signature)]+self.receipts[1:]
  self.assertEqual(verify(self.e,receipts,self.keys)["status"],"INSUFFICIENT_ROOTS")
 def test_mirror_same_root(self):
  keys=dict(self.keys);keys["1"]=Custodian("0",keys["1"].public_key)
  self.assertEqual(verify(self.e,self.receipts,keys)["status"],"INSUFFICIENT_ROOTS")
 def test_jane_gate(self):self.assertFalse(verify(self.e,self.receipts,self.keys)["learning_applied"])
if __name__=="__main__":unittest.main(verbosity=2)
