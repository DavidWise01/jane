import unittest, tempfile, os, copy
from collusion import *
class Experiment(unittest.TestCase):
 def make(self,scenario='agree'):
  reg,c,v=fixtures(scenario);f=FLAY(reg);return f,c,v
 def test_agree(self):
  f,c,v=self.make();self.assertEqual(f.evaluate(c,v)['status'],'CORROBORATED_FIXTURE_CLAIMS')
 def test_collusion_without_acquisition(self):
  f,c,v=self.make('collusion');self.assertEqual(f.evaluate(c,v)['status'],'SHARED_OR_INSUFFICIENT_ACQUISITION_ANCESTRY')
 def test_conflicting_acquisitions(self):
  f,c,v=self.make('conflict');self.assertEqual(f.evaluate(c,v)['status'],'PHYSICAL_SOURCE_CLAIM_CONFLICT')
 def test_conflicting_signed_claims(self):
  f,c,v=self.make('false_claim');self.assertEqual(f.evaluate(c,v)['status'],'CONFLICTING_SIGNED_CLAIMS')
 def test_shared_ancestry(self):
  f,c,v=self.make('shared');self.assertEqual(f.evaluate(c,v)['status'],'SHARED_OR_INSUFFICIENT_ACQUISITION_ANCESTRY')
 def test_two_claim_signatures_not_two_acquisitions(self):
  f,c,v=self.make('collusion');r=f.evaluate(c,v);self.assertEqual(r['claim_signers'],2);self.assertEqual(r['acquisition_signers'],0)
 def test_three_keys_no_physical_truth(self):
  f,c,v=self.make();self.assertFalse(f.evaluate(c,v)['independent_physical_sources_verified'])
 def test_bad_claim_signature(self):
  f,c,v=self.make();c[0]['signature']='00'*64;self.assertEqual(f.evaluate(c,v)['status'],'CLAIM_AUTHENTICATION_INSUFFICIENT')
 def test_bad_voucher_signature(self):
  f,c,v=self.make();v[0]['signature']='00'*64;self.assertNotEqual(f.evaluate(c,v)['status'],'CORROBORATED_FIXTURE_CLAIMS')
 def test_altered_source_claim(self):
  f,c,v=self.make();c[0]['body']['payload']['source_id']='forged';self.assertIn('BAD_SIGNATURE',f.evaluate(c,v)['problems'])
 def test_altered_timestamp(self):
  f,c,v=self.make();v[0]['body']['payload']['timestamp']=2000;self.assertIn('BAD_SIGNATURE',f.evaluate(c,v)['problems'])
 def test_future(self):
  f,c,v=self.make();v[0]=signed('ACQUISITION','acquisition-X',dict(v[0]['body']['payload'],timestamp=1001),seed('acquisition-X'));self.assertIn('STALE_OR_FUTURE',f.evaluate(c,v)['problems'])
 def test_stale(self):
  f,c,v=self.make();v[0]=signed('ACQUISITION','acquisition-X',dict(v[0]['body']['payload'],timestamp=1),seed('acquisition-X'));self.assertIn('STALE_OR_FUTURE',f.evaluate(c,v)['problems'])
 def test_replay(self):
  f,c,v=self.make();f.evaluate(c,v);self.assertIn('REPLAY',f.evaluate(c,v)['problems'])
 def test_replay_restart(self):
  with tempfile.TemporaryDirectory() as td:
   path=os.path.join(td,'audit.db');reg,c,v=fixtures();FLAY(reg,Ledger(path)).evaluate(c,v);self.assertIn('REPLAY',FLAY(reg,Ledger(path)).evaluate(c,v)['problems'])
 def test_local_ledger(self):
  f,c,v=self.make();f.evaluate(c,v);self.assertEqual(f.ledger.audit(),'VALID_LOCAL_CHAIN')
 def test_ledger_tamper(self):
  f,c,v=self.make();f.evaluate(c,v);f.ledger.db.execute("UPDATE events SET kind='forged'");self.assertEqual(f.ledger.audit(),'TAMPERED')
 def test_external_head(self):
  f,c,v=self.make();f.evaluate(c,v);self.assertEqual(f.ledger.audit('a'*64),'EXTERNAL_HEAD_MISMATCH')
 def test_parent_frozen(self):
  f,c,v=self.make();self.assertEqual(f.evaluate(c,v)['active_parent'],'frozen_parent')
 def test_no_learning(self):
  f,c,v=self.make();self.assertFalse(f.evaluate(c,v)['learning_applied'])
 def test_scope(self):
  f,c,v=self.make();self.assertIn('not established',f.evaluate(c,v)['scope'])
 def test_empty_claim(self):
  f,c,v=self.make();self.assertEqual(f.evaluate([],v)['status'],'CLAIM_AUTHENTICATION_INSUFFICIENT')
 def test_empty_vouchers(self):
  f,c,v=self.make();self.assertNotEqual(f.evaluate(c,[])['status'],'CORROBORATED_FIXTURE_CLAIMS')
 def test_duplicate_voucher(self):
  f,c,v=self.make();self.assertIn('REPLAY',f.evaluate(c,[v[0],v[0]])['problems'])
 def test_duplicate_claim(self):
  f,c,v=self.make();self.assertIn('REPLAY',f.evaluate([c[0],c[0]],v)['problems'])
 def test_one_claim_admin(self):
  f,c,v=self.make();f.registry['sensor-B']=Authority('sensor-B','adminA','claimB',pubhex(seed('sensor-B')));self.assertEqual(f.evaluate(c,v)['status'],'CLAIM_AUTHENTICATION_INSUFFICIENT')
 def test_same_voucher_admin(self):
  f,c,v=self.make();f.registry['acquisition-Y']=Authority('acquisition-Y','adminX','acqY',pubhex(seed('acquisition-Y')));self.assertNotEqual(f.evaluate(c,v)['status'],'CORROBORATED_FIXTURE_CLAIMS')
 def test_no_nonce(self):
  f,c,v=self.make();v[0]=signed('ACQUISITION','acquisition-X',dict(v[0]['body']['payload'],nonce=''),seed('acquisition-X'));self.assertIn('INVALID_NONCE',f.evaluate(c,v)['problems'])
 def test_wrong_measurement(self):
  f,c,v=self.make();v[0]=signed('ACQUISITION','acquisition-X',dict(v[0]['body']['payload'],measurement_id='other'),seed('acquisition-X'));self.assertIn('MEASUREMENT_MISMATCH',f.evaluate(c,v)['problems'])
 def test_invalid_kind(self):
  f,c,v=self.make();c[0]=signed('ACQUISITION','sensor-A',c[0]['body']['payload'],seed('sensor-A'));self.assertIn('BAD_SIGNATURE',f.evaluate(c,v)['problems'])
 def test_unknown_issuer(self):
  f,c,v=self.make();c[0]['body']['issuer']='nobody';self.assertIn('INVALID_RECEIPT',f.evaluate(c,v)['problems'])
 def test_determinism(self):
  f,c,v=self.make();r=f.evaluate(c,v);g,d,w=self.make();self.assertEqual(r['digest'],g.evaluate(d,w)['digest'])
 def test_no_silent_change(self):
  f,c,v=self.make();f.evaluate(c,v);self.assertEqual(f.active,'frozen_parent')
 def test_nonce_ledger_persists(self):
  with tempfile.TemporaryDirectory() as td:
   p=os.path.join(td,'l.db');l=Ledger(p);l.record('x','y');self.assertTrue(Ledger(p).seen('x','y'))
 def test_digest_length(self):
  f,c,v=self.make();self.assertEqual(len(f.evaluate(c,v)['digest']),64)
 def test_missing_voucher_then_valid(self):
  f,c,v=self.make();self.assertNotEqual(f.evaluate(c,[])['status'],'CORROBORATED_FIXTURE_CLAIMS');self.assertIn('REPLAY',f.evaluate(c,v)['problems'])
 def test_nonce_scope(self):
  l=Ledger();self.assertTrue(l.record('a','n'));self.assertTrue(l.record('b','n'))
 def test_empty_ledger(self):self.assertEqual(Ledger().audit(),'VALID_LOCAL_CHAIN')
 def test_missing_parent(self):
  f,c,v=self.make();f.ledger.append('X',{});f.ledger.db.execute("UPDATE events SET prev='bad'");self.assertEqual(f.ledger.audit(),'TAMPERED')
 def test_policy_quorum(self):
  with self.assertRaises(ValueError):FLAY({},quorum=0)
 def test_demo(self):self.assertEqual(demo()['scenarios']['agree']['status'],'CORROBORATED_FIXTURE_CLAIMS')
if __name__=='__main__':unittest.main()