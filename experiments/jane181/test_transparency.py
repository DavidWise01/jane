import unittest,tempfile,os,copy
from transparency import *
class TransparencyTests(unittest.TestCase):
 def setUp(self):
  self.ops,self.entries,self.cp,self.receipts=fixture();self.a=Audit(operators=self.ops,required=3)
 def tearDown(self):self.a.close()
 def runcheck(self,cp=None,receipts=None,entries=None,index=2,created=700,minimum=900):
  return self.a.check(cp or self.cp,receipts if receipts is not None else self.receipts,entries if entries is not None else self.entries,index,created,minimum)['status']
 def test_accept(self):self.assertEqual(self.runcheck(),'ANCHORED_INCLUSION_FIXTURE')
 def test_checkpoint_replay(self):self.runcheck();self.assertEqual(self.runcheck(minimum=None),'REPLAY_CHECKPOINT')
 def test_same_checkpoint_nonce_replay_after_restart(self):
  with tempfile.TemporaryDirectory() as d:
   path=os.path.join(d,'db');b=Audit(path,self.ops,3);self.assertEqual(b.check(self.cp,self.receipts,self.entries,2,700)['status'],'ANCHORED_INCLUSION_FIXTURE');b.close();b=Audit(path,self.ops,3);self.assertEqual(b.check(self.cp,self.receipts,self.entries,2,700)['status'],'REPLAY_CHECKPOINT');b.close()
 def test_merkle_six(self):self.assertTrue(verify_inclusion(self.entries[2],2,6,self.cp['root'],proof(self.entries,2)))
 def test_all_inclusions(self):
  for i,e in enumerate(self.entries):self.assertTrue(verify_inclusion(e,i,6,self.cp['root'],proof(self.entries,i)))
 def test_single_leaf(self):
  a=[b'one'];self.assertTrue(verify_inclusion(a[0],0,1,hexh(merkle_root(a)),proof(a,0)))
 def test_odd_leaves(self):
  a=[bytes([i]) for i in range(5)]
  for i in range(5):self.assertTrue(verify_inclusion(a[i],i,5,hexh(merkle_root(a)),proof(a,i)))
 def test_wrong_leaf(self):self.assertFalse(verify_inclusion(b'other',2,6,self.cp['root'],proof(self.entries,2)))
 def test_wrong_index(self):self.assertFalse(verify_inclusion(self.entries[2],1,6,self.cp['root'],proof(self.entries,2)))
 def test_wrong_size(self):self.assertFalse(verify_inclusion(self.entries[2],2,5,self.cp['root'],proof(self.entries,2)))
 def test_wrong_root(self):self.assertFalse(verify_inclusion(self.entries[2],2,6,'a'*64,proof(self.entries,2)))
 def test_tampered_sibling(self):
  p=proof(self.entries,2);p[0]['hash']='a'*64;self.assertFalse(verify_inclusion(self.entries[2],2,6,self.cp['root'],p))
 def test_missing_path(self):self.assertFalse(verify_inclusion(self.entries[2],2,6,self.cp['root'],[]))
 def test_duplicate_path(self):self.assertFalse(verify_inclusion(self.entries[2],2,6,self.cp['root'],proof(self.entries,2)+[{'side':'promoted'}]))
 def test_tampered_raw(self):
  e=list(self.entries);e[2]=b'fabricated';self.assertEqual(self.runcheck(entries=e),'LOG_ROOT_MISMATCH')
 def test_missing_middle(self):self.assertEqual(self.runcheck(entries=self.entries[:2]+self.entries[3:]),'INCOMPLETE_PREFIX')
 def test_missing_suffix(self):self.assertEqual(self.runcheck(entries=self.entries[:-1]),'INCOMPLETE_PREFIX')
 def test_extra_suffix(self):self.assertEqual(self.runcheck(entries=self.entries+[b'x']),'INCOMPLETE_PREFIX')
 def test_invalid_index(self):self.assertEqual(self.runcheck(index=6),'OMITTED_INCLUSION')
 def test_negative_index(self):self.assertEqual(self.runcheck(index=-1),'OMITTED_INCLUSION')
 def test_backdated_external_floor(self):self.assertEqual(self.runcheck(minimum=1100),'BACKDATED_CLAIM')
 def test_claim_postdates_receipt(self):self.assertEqual(self.runcheck(created=1100),'CLAIM_AFTER_OBSERVATION')
 def test_invalid_timestamp(self):
  c=dict(self.cp);c['observed_at']='1000';self.assertEqual(self.runcheck(cp=c),'INVALID_TIME')
 def test_unknown_operator(self):
  r=copy.deepcopy(self.receipts);r[0]['operator']='X';self.assertEqual(self.runcheck(receipts=r),'UNKNOWN_OR_DUPLICATE_OPERATOR')
 def test_duplicate_operator(self):self.assertEqual(self.runcheck(receipts=[self.receipts[0]]*3),'UNKNOWN_OR_DUPLICATE_OPERATOR')
 def test_invalid_signature(self):
  r=copy.deepcopy(self.receipts);r[0]['signature']='00'*64;self.assertEqual(self.runcheck(receipts=r),'BAD_SIGNATURE')
 def test_insufficient(self):self.assertEqual(self.runcheck(receipts=self.receipts[:2]),'INSUFFICIENT_FIXTURE_ROOTS')
 def test_shared_administration(self):
  self.ops['C'].administration='admin_B';self.assertEqual(self.runcheck(),'SHARED_ADMINISTRATION')
 def test_unknown_predecessor(self):
  c=dict(self.cp);c['prev_root']='1'*64;self.assertEqual(self.runcheck(cp=c),'UNKNOWN_PREDECESSOR')
 def test_fork(self):
  self.runcheck();c=dict(self.cp);c['nonce']='second';c['root']='a'*64;r=[v.receipt(c) for v in self.ops.values()];self.assertEqual(self.runcheck(cp=c,receipts=r),'LOG_ROOT_MISMATCH')
 def test_fork_same_size_with_legit_second_tree(self):
  self.runcheck();e=list(self.entries);e[0]=b'changed';c=dict(self.cp);c['nonce']='second';c['root']=hexh(merkle_root(e));r=[v.receipt(c) for v in self.ops.values()];self.assertEqual(self.runcheck(cp=c,receipts=r,entries=e),'EQUIVOCATION')
 def test_rollback(self):
  self.runcheck();e=self.entries[:4];c=dict(self.cp);c.update(size=4,root=hexh(merkle_root(e)),nonce='short');r=[v.receipt(c) for v in self.ops.values()];self.assertEqual(self.runcheck(cp=c,receipts=r,entries=e),'ROLLBACK')
 def test_valid_extension(self):
  self.runcheck();e=self.entries+[b'seven'];c=dict(self.cp);c.update(size=7,root=hexh(merkle_root(e)),prev_root=self.cp['root'],nonce='extended',observed_at=1010);r=[v.receipt(c) for v in self.ops.values()];self.assertEqual(self.runcheck(cp=c,receipts=r,entries=e,index=6),'ANCHORED_INCLUSION_FIXTURE')
 def test_wrong_growth_link(self):
  self.runcheck();e=self.entries+[b'seven'];c=dict(self.cp);c.update(size=7,root=hexh(merkle_root(e)),prev_root='0'*64,nonce='extended',observed_at=1010);r=[v.receipt(c) for v in self.ops.values()];self.assertEqual(self.runcheck(cp=c,receipts=r,entries=e,index=6),'GROWTH_LINK_MISMATCH')
 def test_out_of_order_observation(self):
  self.runcheck();e=self.entries+[b'seven'];c=dict(self.cp);c.update(size=7,root=hexh(merkle_root(e)),prev_root=self.cp['root'],nonce='extended',observed_at=999);r=[v.receipt(c) for v in self.ops.values()];self.assertEqual(self.runcheck(cp=c,receipts=r,entries=e,index=6,minimum=None),'OBSERVATION_ORDER_INVALID')
 def test_replay_nonce_on_distinct_log(self):
  self.runcheck();c=dict(self.cp);c['log_id']='other';r=[v.receipt(c) for v in self.ops.values()];self.assertEqual(self.runcheck(cp=c,receipts=r),'REPLAY_NONCE')
 def test_ledger(self):self.runcheck();self.assertEqual(self.a.ledger(),'VALID_LOCAL_CHAIN')
 def test_ledger_tamper(self):
  self.runcheck();self.a.db.execute("UPDATE evidence SET kind='FORGED' WHERE seq=1");self.a.db.commit();self.assertEqual(self.a.ledger(),'TAMPERED')
 def test_preserve_rejection(self):self.runcheck();self.runcheck(minimum=None);self.assertEqual(self.a.db.execute('SELECT count(*) FROM evidence').fetchone()[0],2)
 def test_reject_does_not_burn_nonce(self):
  self.runcheck(receipts=self.receipts[:1]);self.assertEqual(self.runcheck(),'ANCHORED_INCLUSION_FIXTURE')
 def test_no_real_independence(self):self.assertFalse(demo()['independent_operator_verified'])
 def test_no_learning(self):self.assertFalse(demo()['learning_applied'])
 def test_first_observation_not_proven(self):self.assertFalse(self.a.check(self.cp,self.receipts,self.entries,2,700)['first_observation_proven'])
 def test_digest_determinism(self):self.assertEqual(merkle_root(self.entries),merkle_root(self.entries))
 def test_empty_root(self):self.assertEqual(merkle_root([]),h(b'\x02'+(0).to_bytes(8,'big')+h(b'')))
 def test_bad_proof_index(self):
  with self.assertRaises(ValueError):proof(self.entries,100)
if __name__=='__main__':unittest.main(verbosity=2)