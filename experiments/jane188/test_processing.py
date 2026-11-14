import unittest, tempfile, os
from dataclasses import replace
from processing import *
class ProcessingTests(unittest.TestCase):
 def setUp(self):
  self.ks=keys();self.trust=Trust.fixture(self.ks);self.a=Auditor(trust=self.trust)
  self.msg={'seq':1,'data':b'input'};self.r=receipt(self.ks['receiver'],1,b'input');self.out=H(b'output');self.ex=execution(self.ks['executor'],1,H(b'input'),self.out)
  self.effects=[observation(self.ks[n],n,1,self.out,nonce=n) for n in ('observerA','observerB')]
 def tearDown(self):self.a.close()
 def run_case(self,r=None,e='default',obs=None,msg=None):return self.a.review(msg or self.msg,r or self.r,self.ex if e=='default' else e,self.effects if obs is None else obs)
 def test_receipt_only(self):self.assertEqual(self.a.review(self.msg,self.r),'RECEIPT_ONLY')
 def test_success_claim_only(self):self.assertEqual(self.run_case(obs=[]),'SUCCESS_CLAIM_UNCORROBORATED')
 def test_good(self):self.assertEqual(self.run_case(),'CORROBORATED_FIXTURE_EFFECT')
 def test_replay(self):self.run_case();self.assertEqual(self.run_case(),'REPLAY')
 def test_duplicate_observer(self):self.assertEqual(self.run_case(obs=[self.effects[0],self.effects[0]]),'INVALID_EFFECT_EVIDENCE')
 def test_one_observer(self):self.assertEqual(self.run_case(obs=[self.effects[0]]),'INSUFFICIENT_EFFECT_ANCESTRY')
 def test_same_root(self):
  trust=Trust(self.trust.public,{'observerA':'same','observerB':'same'});a=Auditor(trust=trust)
  self.assertEqual(a.review(self.msg,self.r,self.ex,self.effects),'INSUFFICIENT_EFFECT_ANCESTRY');a.close()
 def test_conflicting_effect(self):
  x=observation(self.ks['observerB'],'observerB',1,H(b'other'),'OBSERVED','b');self.assertEqual(self.run_case(obs=[self.effects[0],x]),'EFFECT_CONFLICT')
 def test_forged_receipt(self):
  r=dict(self.r,signature='00');self.assertEqual(self.run_case(r=r),'UNAUTHENTIC_RECEIPT')
 def test_forged_execution(self):
  x=dict(self.ex,signature='00');self.assertEqual(self.run_case(e=x),'UNAUTHENTIC_EXECUTION_CLAIM')
 def test_forged_effect(self):
  x=dict(self.effects[0],signature='00');self.assertEqual(self.run_case(obs=[x,self.effects[1]]),'INVALID_EFFECT_EVIDENCE')
 def test_tampered_input(self):self.assertEqual(self.run_case(msg={'seq':1,'data':b'tampered'}),'UNAUTHENTIC_RECEIPT')
 def test_wrong_seq(self):self.assertEqual(self.run_case(msg={'seq':2,'data':b'input'}),'UNAUTHENTIC_RECEIPT')
 def test_failed_attempt(self):
  x=execution(self.ks['executor'],1,H(b'input'),self.out,'FAILED');self.assertEqual(self.run_case(e=x),'FAILED_ATTEMPT_PRESERVED')
 def test_wrong_execution_input(self):
  x=execution(self.ks['executor'],1,H(b'other'),self.out);self.assertEqual(self.run_case(e=x),'UNAUTHENTIC_EXECUTION_CLAIM')
 def test_wrong_execution_seq(self):
  x=execution(self.ks['executor'],2,H(b'input'),self.out);self.assertEqual(self.run_case(e=x),'UNAUTHENTIC_EXECUTION_CLAIM')
 def test_wrong_observer_seq(self):
  x=observation(self.ks['observerA'],'observerA',2,self.out);self.assertEqual(self.run_case(obs=[x,self.effects[1]]),'INVALID_EFFECT_EVIDENCE')
 def test_wrong_observer_status(self):
  x=observation(self.ks['observerA'],'observerA',1,self.out,'UNKNOWN');self.assertEqual(self.run_case(obs=[x,self.effects[1]]),'INVALID_EFFECT_EVIDENCE')
 def test_unknown_observer(self):
  x={'signer':'unknown','body':self.effects[0]['body'],'signature':self.effects[0]['signature']};self.assertEqual(self.run_case(obs=[x,self.effects[1]]),'INVALID_EFFECT_EVIDENCE')
 def test_wrong_receipt_signer(self):
  x=dict(self.r,signer='executor');self.assertEqual(self.run_case(r=x),'UNAUTHENTIC_RECEIPT')
 def test_wrong_execution_signer(self):
  x=dict(self.ex,signer='receiver');self.assertEqual(self.run_case(e=x),'UNAUTHENTIC_EXECUTION_CLAIM')
 def test_output_malformed(self):
  x=execution(self.ks['executor'],1,H(b'input'),'short');self.assertEqual(self.run_case(e=x),'MALFORMED_OUTPUT_COMMITMENT')
 def test_both_signatures_different(self):self.assertNotEqual(self.effects[0]['signature'],self.effects[1]['signature'])
 def test_no_activation(self):self.assertIn('frozen_parent',self.a.db.execute('select payload from audit').fetchone()[0] if self.run_case() else '')
 def test_ledger(self):self.run_case();self.assertTrue(self.a.ledger_ok())
 def test_tamper_ledger(self):
  self.run_case();self.a.db.execute("update audit set payload='{}' where idx=1");self.a.db.commit();self.assertFalse(self.a.ledger_ok())
 def test_persistent_replay(self):
  fd,path=tempfile.mkstemp();os.close(fd)
  try:
   a=Auditor(path,self.trust);self.assertEqual(a.review(self.msg,self.r,self.ex,self.effects),'CORROBORATED_FIXTURE_EFFECT');a.close()
   b=Auditor(path,self.trust);self.assertEqual(b.review(self.msg,self.r,self.ex,self.effects),'REPLAY');b.close()
  finally:os.unlink(path)
 def test_demo(self):
  d=demo();self.assertEqual(d['independent_fixture_effects'],'CORROBORATED_FIXTURE_EFFECT');self.assertTrue(d['ledger_ok'])
 def test_deterministic(self):self.assertEqual(demo(),demo())
 def test_hash_64(self):self.assertEqual(len(self.out),64)
 def test_wrong_body_type(self):self.assertFalse(verify(self.ks['receiver'].public_key(),{'test':1},'bad'))
 def test_empty_effects_default(self):self.assertEqual(self.run_case(obs=[]),'SUCCESS_CLAIM_UNCORROBORATED')
 def test_no_trust(self):
  with self.assertRaises(ValueError):Auditor()
 def test_repeat_failed_record(self):
  x=execution(self.ks['executor'],1,H(b'input'),self.out,'FAILED');self.run_case(e=x);self.assertEqual(self.run_case(e=x),'REPLAY')
 def test_distinct_effect_nonce(self):self.assertNotEqual(self.effects[0]['body']['nonce'],self.effects[1]['body']['nonce'])
 def test_status_never_physical(self):self.assertNotIn('PHYSICAL',self.run_case())
if __name__=='__main__':unittest.main(verbosity=2)