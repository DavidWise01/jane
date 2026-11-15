import unittest,tempfile,os
from factory import FLAY221,Audit,fixture,seal,digest,Policy
class TestFactory(unittest.TestCase):
 def inspect(self, mode='consistent'):return FLAY221().inspect(fixture(mode))['verdict']
 def test_consistent(self):self.assertEqual(self.inspect(),'DECLARED_PRODUCTION_OBSERVATIONS_CONSISTENT_FIXTURE')
 def test_factory_only(self):self.assertEqual(self.inspect('factory_only'),'NO_PRODUCTION_OBSERVATION')
 def test_document_copies(self):self.assertEqual(self.inspect('document_copies'),'DOCUMENT_ONLY_CORROBORATION')
 def test_shared_root(self):self.assertEqual(self.inspect('shared_root'),'SHARED_PRODUCTION_ANCESTRY')
 def test_shared_instrument(self):self.assertEqual(self.inspect('shared_instrument'),'SHARED_PRODUCTION_ANCESTRY')
 def test_wrong_process(self):self.assertEqual(self.inspect('wrong_process'),'PROCESS_DISAGREEMENT')
 def test_late(self):self.assertEqual(self.inspect('late_sensor'),'OBSERVATION_TIME_INVALID')
 def test_forged_observer(self):self.assertEqual(self.inspect('forged_observer'),'INVALID_OBSERVER_SIGNATURE')
 def test_duplicate_witness(self):self.assertEqual(self.inspect('duplicate_witness'),'DUPLICATE_WITNESS')
 def test_bad_claim_signature(self):
  f=fixture();f['factory_claim']['signature']='00'*64;self.assertEqual(FLAY221().inspect(f)['verdict'],'INVALID_SIGNATURE')
 def test_bad_order_signature(self):
  f=fixture();f['order']['signature']='00'*64;self.assertEqual(FLAY221().inspect(f)['verdict'],'INVALID_SIGNATURE')
 def test_bad_checkpoint_signature(self):
  f=fixture();f['checkpoint']['signature']='00'*64;self.assertEqual(FLAY221().inspect(f)['verdict'],'INVALID_SIGNATURE')
 def test_identity(self):
  f=fixture();f['order']=seal(dict(f['order']['body'],device='FAKE'),'ordering');self.assertEqual(FLAY221().inspect(f)['verdict'],'IDENTITY_MISMATCH')
 def test_observation_identity(self):
  f=fixture();f['observations'][0]=seal(dict(f['observations'][0]['body'],unit='FAKE'),'w1');self.assertEqual(FLAY221().inspect(f)['verdict'],'OBSERVED_IDENTITY_MISMATCH')
 def test_observation_claim(self):
  f=fixture();f['observations'][0]=seal(dict(f['observations'][0]['body'],claim_digest='fake'),'w1');self.assertEqual(FLAY221().inspect(f)['verdict'],'OBSERVATION_CLAIM_MISMATCH')
 def test_checkpoint_digest(self):
  f=fixture();f['checkpoint']=seal(dict(f['checkpoint']['body'],order_digest='fake'),'ledger');self.assertEqual(FLAY221().inspect(f)['verdict'],'CHECKPOINT_MISMATCH')
 def test_checkpoint_observers(self):
  f=fixture();f['checkpoint']=seal(dict(f['checkpoint']['body'],observer_digests=[]),'ledger');self.assertEqual(FLAY221().inspect(f)['verdict'],'CHECKPOINT_MISMATCH')
 def test_chronology(self):
  f=fixture();f['order']=seal(dict(f['order']['body'],timestamp=111),'ordering');self.assertEqual(FLAY221().inspect(f)['verdict'],'CHECKPOINT_MISMATCH')
 def test_short_nonce(self):
  self.assertEqual(FLAY221().inspect(fixture(nonce='abc'))['verdict'],'INVALID_NONCE')
 def test_empty_observations(self):self.assertEqual(self.inspect('factory_only'),'NO_PRODUCTION_OBSERVATION')
 def test_one_observation(self):
  f=fixture();f['observations']=f['observations'][:1];self.assertEqual(FLAY221().inspect(f)['verdict'],'INSUFFICIENT_WITNESSES')
 def test_policy_three(self):
  self.assertEqual(FLAY221(policy=Policy(3,3)).inspect(fixture())['verdict'],'INSUFFICIENT_WITNESSES')
 def test_replay(self):
  a=Audit();v=FLAY221(a);f=fixture();self.assertEqual(v.inspect(f)['verdict'],'DECLARED_PRODUCTION_OBSERVATIONS_CONSISTENT_FIXTURE');self.assertEqual(v.inspect(f)['verdict'],'REPLAY');a.close()
 def test_replay_restart(self):
  with tempfile.TemporaryDirectory() as d:
   p=os.path.join(d,'log.sqlite');a=Audit(p);self.assertIn('FIXTURE',FLAY221(a).inspect(fixture())['verdict']);a.close()
   a=Audit(p);self.assertEqual(FLAY221(a).inspect(fixture())['verdict'],'REPLAY');a.close()
 def test_tamper(self):
  a=Audit();v=FLAY221(a);v.inspect(fixture());a.db.execute("UPDATE events SET hash='forged' WHERE n=1");a.db.commit();self.assertEqual(v.inspect(fixture(nonce='challenge-221-0002'))['verdict'],'CORRUPT_LOG');a.close()
 def test_frozen_parent(self):self.assertFalse(FLAY221().inspect(fixture())['jane_parent_mutated'])
 def test_no_physical_proof(self):self.assertFalse(FLAY221().inspect(fixture())['physical_manufacture_verified'])
 def test_bad_packet(self):self.assertEqual(FLAY221().inspect({})['verdict'],'INVALID_PACKET')
 def test_invalid_observer_actor(self):
  f=fixture();f['observations'][0]=seal(dict(f['observations'][0]['body'],actor='unknown'),'unknown');self.assertEqual(FLAY221().inspect(f)['verdict'],'INVALID_OBSERVER_SIGNATURE')
 def test_different_nonce_changes_packet(self):self.assertNotEqual(digest(fixture(nonce='challenge-221-0001')),digest(fixture(nonce='challenge-221-0002')))
if __name__=='__main__':unittest.main()