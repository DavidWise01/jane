import unittest, tempfile, os
from dataclasses import replace
from coverage import FLAY,Signed,keys,fixture,commitment,hashof,tree_root,demo

class CoverageTests(unittest.TestCase):
 def setUp(self):
  (sk,rk),self.s,self.w,self.rs=fixture();self.f=FLAY(sk,rk)
 def tearDown(self):self.f.close()
 def runaudit(self):return self.f.audit(self.s,self.w,self.rs)['status']
 def resign_w(self,**changes):
  _,rk=keys();b={**self.w.body,**changes};self.w=Signed.issue(rk,b)
 def resign_s(self,**changes):
  sk,_=keys();b={**self.s.body,**changes};self.s=Signed.issue(sk,b)
 def test_complete(self):self.assertEqual(self.runaudit(),'COMPLETE_SIGNED_INBOX_FIXTURE')
 def test_gap(self):
  (sk,rk),s,w,rs=fixture((1,3));self.assertEqual(self.f.audit(s,w,rs)['status'],'WATERMARK_COVERAGE_GAP')
 def test_gap_index(self):
  (sk,rk),s,w,rs=fixture((1,3));self.assertEqual(self.f.audit(s,w,rs)['missing'],[2])
 def test_empty(self):
  (sk,rk),s,w,rs=fixture(());self.assertEqual(self.f.audit(s,w,rs)['missing'],[1,2,3])
 def test_forged_watermark(self):self.w=replace(self.w,signature='aa'*64);self.assertEqual(self.runaudit(),'BAD_WATERMARK_SIGNATURE')
 def test_forged_sender(self):self.s=replace(self.s,signature='aa'*64);self.assertEqual(self.runaudit(),'BAD_SENDER_SIGNATURE')
 def test_forged_ack(self):self.rs[0]=replace(self.rs[0],signature='aa'*64);self.assertEqual(self.runaudit(),'BAD_ACK_SIGNATURE')
 def test_changed_ack(self):self.rs[0]=replace(self.rs[0],body={**self.rs[0].body,'seq':2});self.assertEqual(self.runaudit(),'BAD_ACK_SIGNATURE')
 def test_omission_after_commit(self):self.rs.pop(1);self.assertEqual(self.runaudit(),'INBOX_COMMITMENT_MISMATCH')
 def test_reorder_after_commit(self):self.rs.reverse();self.assertEqual(self.runaudit(),'INBOX_COMMITMENT_MISMATCH')
 def test_wrong_size(self):self.resign_w(count=2);self.assertEqual(self.runaudit(),'INBOX_COMMITMENT_MISMATCH')
 def test_wrong_root(self):self.resign_w(inbox_commitment='0'*64);self.assertEqual(self.runaudit(),'INBOX_COMMITMENT_MISMATCH')
 def test_different_sender(self):self.resign_w(sender_digest='f'*64);self.assertEqual(self.runaudit(),'WATERMARK_SCOPE_MISMATCH')
 def test_watermark_too_high(self):self.resign_w(through=4);self.assertEqual(self.runaudit(),'WATERMARK_SCOPE_MISMATCH')
 def test_watermark_too_low(self):self.resign_w(through=2);self.assertEqual(self.runaudit(),'WATERMARK_SCOPE_MISMATCH')
 def test_old_watermark(self):self.resign_w(issued_at=1);self.assertEqual(self.runaudit(),'STALE_OR_FUTURE_WATERMARK')
 def test_future_watermark(self):self.resign_w(issued_at=1500);self.assertEqual(self.runaudit(),'STALE_OR_FUTURE_WATERMARK')
 def test_missing_nonce(self):self.resign_w(nonce='');self.assertEqual(self.runaudit(),'INVALID_NONCE')
 def test_wrong_domain(self):self.resign_w(domain='wrong');self.assertEqual(self.runaudit(),'BAD_DOMAIN')
 def test_wrong_sender_domain(self):self.resign_s(domain='wrong');self.assertEqual(self.runaudit(),'BAD_DOMAIN')
 def test_sender_invalid_range(self):self.resign_s(end=0);self.assertEqual(self.runaudit(),'INVALID_RANGE')
 def test_sender_changed_manifest_breaks_ack_context(self):
  self.resign_s(payload_hashes=[]);self.resign_w(sender_digest=hashof(self.s.body));self.assertEqual(self.runaudit(),'BAD_ACK_CONTEXT')
 def test_ack_context(self):
  _,rk=keys();self.rs[0]=Signed.issue(rk,{**self.rs[0].body,'sender_digest':'bad'});self.assertEqual(self.runaudit(),'BAD_ACK_CONTEXT')
 def test_payload_mismatch(self):
  _,rk=keys();self.rs[0]=Signed.issue(rk,{**self.rs[0].body,'payload_hash':'f'*64});self.assertEqual(self.runaudit(),'INBOX_COMMITMENT_MISMATCH')
 def test_duplicate_ack(self):self.rs.append(self.rs[0]);self.assertEqual(self.runaudit(),'DUPLICATE_ACK')
 def test_conflicting_ack(self):
  _,rk=keys();self.rs.append(Signed.issue(rk,{**self.rs[0].body,'payload_hash':'a'*64}));self.assertEqual(self.runaudit(),'CONFLICTING_ACK')
 def test_out_of_range(self):
  _,rk=keys();self.rs.append(Signed.issue(rk,{**self.rs[0].body,'seq':4}));self.assertEqual(self.runaudit(),'OUT_OF_RANGE_ACK')
 def test_replay(self):self.assertEqual(self.runaudit(),'COMPLETE_SIGNED_INBOX_FIXTURE');self.assertEqual(self.runaudit(),'REPLAY_WATERMARK')
 def test_replay_across_restart(self):
  fd,p=tempfile.mkstemp();os.close(fd)
  try:
   sk,rk=self.f.sender,self.f.receiver
   x=FLAY(sk,rk,p);self.assertEqual(x.audit(self.s,self.w,self.rs)['status'],'COMPLETE_SIGNED_INBOX_FIXTURE');x.close()
   y=FLAY(sk,rk,p);self.assertEqual(y.audit(self.s,self.w,self.rs)['status'],'REPLAY_WATERMARK');y.close()
  finally:os.unlink(p)
 def test_chain_valid(self):self.runaudit();self.assertTrue(self.f.ledger.check())
 def test_tamper_chain(self):self.runaudit();self.f.ledger.db.execute("UPDATE audit SET head=? WHERE id=1",('f'*64,));self.f.ledger.db.commit();self.assertFalse(self.f.ledger.check())
 def test_single_entry(self):
  (sk,rk),s,w,rs=fixture((1,),through=1);self.assertEqual(self.f.audit(s,w,rs)['status'],'COMPLETE_SIGNED_INBOX_FIXTURE')
 def test_tree_size_bound(self):self.assertNotEqual(commitment([{'x':1}]),commitment([{'x':1},{'x':1}]))
 def test_tree_order(self):self.assertNotEqual(commitment([{'x':1},{'x':2}]),commitment([{'x':2},{'x':1}]))
 def test_tree_empty(self):self.assertEqual(len(tree_root([])),64)
 def test_no_autolearn(self):self.assertFalse(self.f.audit(self.s,self.w,self.rs)['automatic_learning'])
 def test_parent_frozen(self):self.assertEqual(self.f.active,'frozen_parent')
 def test_no_physical_independence(self):self.assertFalse(self.f.audit(self.s,self.w,self.rs)['independent_physical_custody'])
 def test_deterministic_demo(self):self.assertEqual(demo(),demo())
 def test_gap_does_not_replay_as_valid(self):
  (sk,rk),s,w,rs=fixture((1,3));self.assertEqual(self.f.audit(s,w,rs)['status'],'WATERMARK_COVERAGE_GAP');self.assertEqual(self.f.audit(s,w,rs)['status'],'REPLAY_WATERMARK')

if __name__=='__main__':unittest.main(verbosity=2)
