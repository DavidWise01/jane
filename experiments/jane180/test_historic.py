import unittest,tempfile,os,copy
from historic import *
class HistoricTests(unittest.TestCase):
 def setUp(self):
  self.f=fixture();self.a=HistoricAudit({'scheduler':pub(self.f['decision_key'])},self.f['registry']);self.d=self.f['decision'];self.anchors=self.f['anchors']()
 def tearDown(self):self.a.close()
 def evaluate(self,d=None,anchors=None,risk=(100,200),**kw):return self.a.evaluate(self.d if d is None else d,self.anchors if anchors is None else anchors,risk,**kw)
 def test_valid_pre_risk_anchor(self):self.assertEqual(self.evaluate()['verdict'],'PRE_RISK_ANCHORED_FIXTURE')
 def test_all_three_fixture_roots(self):self.assertEqual(self.evaluate()['accepted_fixture_roots'],3)
 def test_no_learning(self):self.assertFalse(self.evaluate()['learning_applied'])
 def test_parent_frozen(self):self.assertEqual(self.evaluate()['active_parent'],'FROZEN')
 def test_no_independence_proof(self):self.assertFalse(self.evaluate()['independence_verified'])
 def test_anchored_checkpoint(self):self.assertEqual(self.evaluate(expected_checkpoint='a'*64)['verdict'],'PRE_RISK_ANCHORED_FIXTURE')
 def test_mismatch_expected(self):self.assertEqual(self.evaluate(expected_checkpoint='b'*64)['verdict'],'CHECKPOINT_MISMATCH')
 def test_late_anchor_not_pre_risk(self):self.assertEqual(self.evaluate(anchors=self.f['anchors'](at=150))['verdict'],'HISTORIC_SIGNATURE_UNCORROBORATED')
 def test_late_anchor_finding(self):self.assertIn('ANCHOR_NOT_PREDATING_RISK',self.evaluate(anchors=self.f['anchors'](at=150))['findings'])
 def test_claim_in_compromise_interval(self):
  d=receipt('scheduler',self.f['decision_key'],{**self.d['payload'],'claimed_time':150});self.assertEqual(self.evaluate(d=d)['verdict'],'POTENTIALLY_ATTACKER_AUTHORED')
 def test_claim_after_compromise(self):
  d=receipt('scheduler',self.f['decision_key'],{**self.d['payload'],'claimed_time':250});self.assertEqual(self.evaluate(d=d)['verdict'],'POST_RISK_OLD_KEY_UNTRUSTED')
 def test_forged_decision(self):
  d=copy.deepcopy(self.d);d['payload']['claimed_time']=3;self.assertEqual(self.evaluate(d=d)['verdict'],'INVALID_DECISION_SIGNATURE')
 def test_malformed_decision(self):
  d=receipt('scheduler',self.f['decision_key'],{**self.d['payload'],'seq':'x'});self.assertEqual(self.evaluate(d=d)['verdict'],'MALFORMED_DECISION')
 def test_forged_anchor(self):
  anchors=copy.deepcopy(self.anchors);anchors[0]['payload']['head']='b'*64;r=self.evaluate(anchors=anchors);self.assertIn('INVALID_ANCHOR_SIGNATURE',r['findings'])
 def test_missing_roots(self):self.assertEqual(self.evaluate(anchors=self.anchors[:1])['verdict'],'HISTORIC_SIGNATURE_UNCORROBORATED')
 def test_two_roots_sufficient(self):self.assertEqual(self.evaluate(anchors=self.anchors[:2])['verdict'],'PRE_RISK_ANCHORED_FIXTURE')
 def test_duplicate_anchor(self):self.assertIn('DUPLICATE_ANCHOR',self.evaluate(anchors=self.anchors[:2]+[self.anchors[0]])['findings'])
 def test_shared_administration(self):
  self.f['registry']['custodyB']['admin']='custodyA';r=self.evaluate();self.assertIn('SHARED_CUSTODY_ANCESTRY',r['findings'])
 def test_shared_root(self):
  self.f['registry']['custodyB']['root']='custodyA';r=self.evaluate();self.assertIn('SHARED_CUSTODY_ANCESTRY',r['findings'])
 def test_forged_head_conflict(self):
  ar=self.f['anchors']();ar[0]=receipt('custodyA',self.f['keys']['custodyA'],{**ar[0]['payload'],'head':'b'*64});self.assertEqual(self.evaluate(anchors=ar)['verdict'],'CONFLICTING_ANCHORS')
 def test_wrong_decision_id(self):
  ar=self.f['anchors']();ar[0]=receipt('custodyA',self.f['keys']['custodyA'],{**ar[0]['payload'],'decision_id':'other'});self.assertEqual(self.evaluate(anchors=ar)['verdict'],'CONFLICTING_ANCHORS')
 def test_impossible_time(self):
  ar=self.f['anchors']();ar[0]=receipt('custodyA',self.f['keys']['custodyA'],{**ar[0]['payload'],'recorded_before':2});self.assertIn('IMPOSSIBLE_ANCHOR_TIME',self.evaluate(anchors=ar)['findings'])
 def test_anchor_budget(self):
  small=HistoricAudit({'scheduler':pub(self.f['decision_key'])},self.f['registry'],policy=Policy(max_depth=2));r=small.evaluate(self.d,self.anchors,(100,200));small.close();self.assertIn('ANCHOR_BUDGET_EXCEEDED',r['findings'])
 def test_valid_local_chain(self):self.evaluate();self.assertEqual(self.a.audit_chain(),'VALID_LOCAL_CHAIN')
 def test_external_head_matches(self):self.evaluate();self.assertEqual(self.a.audit_chain(self.a._head()[1]),'VALID_LOCAL_CHAIN')
 def test_external_head_mismatch(self):self.evaluate();self.assertEqual(self.a.audit_chain('0'*64),'EXTERNAL_HEAD_MISMATCH')
 def test_tampered_ledger(self):
  self.evaluate();self.a.conn.execute("update audits set body='{}'");self.a.conn.commit();self.assertEqual(self.a.audit_chain(),'TAMPERED')
 def test_second_evaluation_retained(self):self.evaluate();self.evaluate();self.assertEqual(self.a._head()[0],2)
 def test_deterministic_verdict(self):self.assertEqual(self.evaluate()['digest'],self.evaluate()['digest'])
 def test_persist_restart(self):
  with tempfile.TemporaryDirectory() as t:
   path=os.path.join(t,'history.sqlite');x=HistoricAudit({'scheduler':pub(self.f['decision_key'])},self.f['registry'],db=path);x.evaluate(self.d,self.anchors,(100,200));head=x._head()[1];x.close();y=HistoricAudit({'scheduler':pub(self.f['decision_key'])},self.f['registry'],db=path);self.assertEqual(y.audit_chain(head),'VALID_LOCAL_CHAIN');y.close()
 def test_empty_chain(self):self.assertEqual(self.a.audit_chain(),'VALID_LOCAL_CHAIN')
 def test_bad_policy_minimum(self):
  with self.assertRaises(ValueError):Policy(required_custodians=1)
 def test_bad_policy_depth(self):
  with self.assertRaises(ValueError):Policy(max_depth=0)
 def test_digest_is_sha256(self):self.assertEqual(len(self.evaluate()['digest']),64)
 def test_demo_all_scenarios(self):self.assertEqual(demo()['audit'],'VALID_LOCAL_CHAIN')
 def test_historic_claim_not_current(self):self.assertNotIn('CURRENT',self.evaluate()['verdict'])
 def test_retained_before_risk(self):self.assertEqual(self.anchors[0]['payload']['recorded_before'],66)
 def test_signature_valid(self):self.assertTrue(valid(pub(self.f['decision_key']),self.d['payload'],self.d['signature']))
 def test_signature_invalid(self):self.assertFalse(valid(pub(self.f['decision_key']),self.d['payload'],'bad'))
 def test_bad_risk_interval(self):self.assertEqual(self.evaluate(risk=(200,100))['verdict'],'INVALID_COMPROMISE_INTERVAL')
 def test_boundary_anchor_equals_start_not_early(self):self.assertIn('ANCHOR_NOT_PREDATING_RISK',self.evaluate(anchors=self.f['anchors'](at=99))['findings'])
 def test_report_retained_past(self):self.assertIn('compromise_interval',self.evaluate())
 def test_not_physical_execution(self):self.assertIn('no physical execution proof',self.evaluate()['scope'])
if __name__=='__main__':unittest.main(verbosity=2)