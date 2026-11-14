import unittest,tempfile,os,hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from reconcile import *
class Tests(unittest.TestCase):
 def setUp(self):
  self.sp=Ed25519PrivateKey.from_private_bytes(bytes([1])*32);self.rp=Ed25519PrivateKey.from_private_bytes(bytes([2])*32)
  self.keys={'sender':self.sp.public_key(),'receiver':self.rp.public_key()}
  self.h=hashlib.sha256(b'a').hexdigest()
  self.sent=sign(self.sp,'sender','outbox','s',{'seq':1,'payload_hash':self.h,'sent':w(0,10)})
  self.ack=lambda lo,hi=0:sign(self.rp,'receiver','ack',f'a{lo}',{'seq':1,'payload_hash':self.h,'received':w(lo,hi or lo)})
  self.wm=lambda seq=1:sign(self.rp,'receiver','watermark','wm',{'through':seq,'observed':w(700,710)})
  self.out=lambda lo,hi:sign(self.rp,'receiver','outage','out',{'start':w(lo,lo),'end':w(hi,hi)})
 def test_demo(self):self.assertEqual(demo()['status'],'ACK_EVIDENCE_GAP')
 def test_demo_audit(self):self.assertTrue(demo()['audit_valid'])
 def test_ontime(self):self.assertEqual(reconcile([self.sent],[self.ack(200)],now=800)['status'],'FULLY_ACKNOWLEDGED_FIXTURE')
 def test_late(self):self.assertEqual(reconcile([self.sent],[self.ack(400)],now=800)['status'],'LATE_DELIVERY_CONFIRMED_FIXTURE')
 def test_overlap(self):self.assertEqual(reconcile([self.sent],[self.ack(305,315)],now=800)['status'],'TIMING_UNCERTAIN')
 def test_missing_overdue(self):self.assertEqual(reconcile([self.sent],[],now=800)['status'],'OVERDUE_UNOBSERVED')
 def test_missing_predeadline(self):self.assertEqual(reconcile([self.sent],[],now=30)['status'],'PENDING')
 def test_deadline_uncertain(self):self.assertEqual(reconcile([self.sent],[],now=305)['items'][0]['status'],'DEADLINE_UNCERTAIN')
 def test_watermark_gap(self):self.assertEqual(reconcile([self.sent],[],self.wm(),now=800)['status'],'ACK_EVIDENCE_GAP')
 def test_watermark_before(self):self.assertEqual(reconcile([self.sent],[],self.wm(0),now=800)['status'],'OVERDUE_UNOBSERVED')
 def test_outage(self):self.assertEqual(reconcile([self.sent],[],None,[self.out(200,700)],now=800)['status'],'OUTAGE_OBSCURES_DELIVERY')
 def test_outage_before(self):self.assertEqual(reconcile([self.sent],[],None,[self.out(900,950)],now=800)['status'],'OVERDUE_UNOBSERVED')
 def test_outage_overrides_gap(self):self.assertEqual(reconcile([self.sent],[],self.wm(),[self.out(200,700)],now=800)['status'],'OUTAGE_OBSCURES_DELIVERY')
 def test_payload_mismatch(self):
  bad=sign(self.rp,'receiver','ack','bad',{'seq':1,'payload_hash':'f'*64,'received':w(200,200)})
  self.assertEqual(reconcile([self.sent],[bad])['status'],'ACK_PAYLOAD_CONFLICT')
 def test_conflicting_ack(self):self.assertEqual(reconcile([self.sent],[self.ack(200),self.ack(400)])['status'],'ACK_CONFLICT')
 def test_unknown_ack(self):
  a=sign(self.rp,'receiver','ack','unknown',{'seq':2,'payload_hash':self.h,'received':w(200,200)})
  self.assertEqual(reconcile([self.sent],[a])['status'],'UNKNOWN_ACK')
 def test_empty_outbox(self):self.assertEqual(reconcile([],[])['status'],'NO_OUTBOX')
 def test_gap_outbox(self):
  s3=sign(self.sp,'sender','outbox','s3',{'seq':3,'payload_hash':self.h,'sent':w(0,10)})
  self.assertEqual(reconcile([self.sent,s3],[])['status'],'OUTBOX_GAP')
 def test_wrong_kind_outbox(self):
  with self.assertRaises(ValueError):reconcile([self.ack(100)],[])
 def test_wrong_kind_ack(self):
  with self.assertRaises(ValueError):reconcile([self.sent],[self.sent])
 def test_wrong_kind_outage(self):
  with self.assertRaises(ValueError):reconcile([self.sent],[],outages=[self.sent])
 def test_wrong_watermark(self):
  with self.assertRaises(ValueError):reconcile([self.sent],[],self.sent)
 def test_clock_invalid(self):
  with self.assertRaises(ValueError):window(w(2,1))
 def test_clock_float(self):
  with self.assertRaises(ValueError):window(w(1.0,3))
 def test_bad_deadline(self):
  with self.assertRaises(ValueError):FLAY(':memory:',self.keys,deadline_ms=0)
 def test_receive_valid(self):
  f=FLAY(':memory:',self.keys);self.assertEqual(f.receive(self.sent),'ACCEPTED_RECEIPT');f.close()
 def test_replay(self):
  f=FLAY(':memory:',self.keys);f.receive(self.sent);self.assertEqual(f.receive(self.sent),'REPLAY');f.close()
 def test_nonce_equivocation(self):
  f=FLAY(':memory:',self.keys);f.receive(self.sent)
  r=sign(self.sp,'sender','outbox','s',{'seq':1,'payload_hash':'0'*64,'sent':w(0,10)})
  self.assertEqual(f.receive(r),'NONCE_EQUIVOCATION');f.close()
 def test_persistent_replay(self):
  with tempfile.TemporaryDirectory() as t:
   db=os.path.join(t,'test.db');f=FLAY(db,self.keys);f.receive(self.sent);f.close()
   f=FLAY(db,self.keys);self.assertEqual(f.receive(self.sent),'REPLAY');f.close()
 def test_bad_signature(self):
  f=FLAY(':memory:',self.keys);fake=sign(self.rp,'sender','outbox','fake',self.sent.body)
  self.assertEqual(f.receive(fake),'BAD_SIGNATURE_OR_KIND');f.close()
 def test_ledger_tamper(self):
  f=FLAY(':memory:',self.keys);f.receive(self.sent);self.assertTrue(f.check_chain())
  f.db.execute('UPDATE audit SET event=? WHERE seq=1',('x',));f.db.commit();self.assertFalse(f.check_chain());f.close()
 def test_invalid_receipt_body(self):
  f=FLAY(':memory:',self.keys);r=sign(self.sp,'sender','outbox','bad',{'seq':0,'payload_hash':self.h,'sent':w(0,1)})
  self.assertEqual(f.receive(r),'INVALID_BODY');f.close()
 def test_no_promotion(self):self.assertFalse(demo()['learning_applied'])
 def test_frozen_parent(self):self.assertEqual(demo()['active'],'frozen_parent')
 def test_no_culpability(self):self.assertEqual(demo()['cause'],'NOT_ESTABLISHED')
 def test_deterministic(self):self.assertEqual(demo(),demo())
if __name__=='__main__':unittest.main(verbosity=2)