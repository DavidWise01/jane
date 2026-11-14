import unittest
from dataclasses import replace
from policy import Evidence,Policy,Audit,evaluate,fixture,digest

E=Evidence(1000,1003,True,True,True,'a'*64,'b'*64)
P1=Policy('v1',5)
P2=Policy('v2',2)

class PolicyTests(unittest.TestCase):
    def test_01_old_accepts(self):self.assertEqual(evaluate(E,P1)['verdict'],'DECLARED_FIXTURE_MATCH')
    def test_02_new_rejects(self):self.assertEqual(evaluate(E,P2)['verdict'],'REJECTED')
    def test_03_delta(self):self.assertEqual(evaluate(E,P1)['delta'],3)
    def test_04_failure(self):self.assertIn('OUTSIDE_TOLERANCE',evaluate(E,P2)['failures'])
    def test_05_status(self):self.assertEqual(fixture()[1]['status'],'POLICY_INDUCED_VERDICT_CHANGE')
    def test_06_changed(self):self.assertTrue(fixture()[1]['policy_changed'])
    def test_07_verdict_changed(self):self.assertTrue(fixture()[1]['verdict_changed'])
    def test_08_same_evidence(self):
        r=fixture()[1];self.assertEqual(r['old']['evidence_digest'],r['new']['evidence_digest'])
    def test_09_distinct_policies(self):self.assertNotEqual(evaluate(E,P1)['policy_digest'],evaluate(E,P2)['policy_digest'])
    def test_10_policy_same(self):self.assertEqual(Audit(E,P1,P1).run()['status'],'POLICY_UNCHANGED')
    def test_11_policy_changed_stable(self):self.assertEqual(Audit(E,P1,Policy('v3',6)).run()['status'],'POLICY_CHANGED_VERDICT_STABLE')
    def test_12_exact_tolerance(self):self.assertEqual(evaluate(E,Policy('v',3))['verdict'],'DECLARED_FIXTURE_MATCH')
    def test_13_zero_tolerance(self):self.assertEqual(evaluate(E,Policy('v',0))['verdict'],'REJECTED')
    def test_14_negative_tolerance(self):
        with self.assertRaises(ValueError):Policy('x',-1)
    def test_15_noninteger_tolerance(self):
        with self.assertRaises(ValueError):Policy('x',2.5)
    def test_16_bool_tolerance(self):
        with self.assertRaises(ValueError):Policy('x',True)
    def test_17_version_invalid(self):
        with self.assertRaises(ValueError):Policy('not valid',5)
    def test_18_reuse_version(self):
        with self.assertRaises(ValueError):Audit(E,P1,Policy('v1',2))
    def test_19_question_drift(self):self.assertIn('QUESTION_DRIFT',evaluate(replace(E,same_question=False),P1)['failures'])
    def test_20_selection_drift(self):self.assertIn('SELECTION_DRIFT',evaluate(replace(E,same_selection=False),P1)['failures'])
    def test_21_ancestry(self):self.assertIn('SHARED_ANCESTRY',evaluate(replace(E,distinct_declared_roots=False),P1)['failures'])
    def test_22_disable_question_rule(self):self.assertNotIn('QUESTION_DRIFT',evaluate(replace(E,same_question=False),replace(P1,require_question_match=False))['failures'])
    def test_23_disable_selection_rule(self):self.assertNotIn('SELECTION_DRIFT',evaluate(replace(E,same_selection=False),replace(P1,require_selection_match=False))['failures'])
    def test_24_disable_ancestry_rule(self):self.assertNotIn('SHARED_ANCESTRY',evaluate(replace(E,distinct_declared_roots=False),replace(P1,require_distinct_roots=False))['failures'])
    def test_25_multi_failure(self):self.assertEqual(len(evaluate(replace(E,same_question=False,same_selection=False),P2)['failures']),3)
    def test_26_bad_capture(self):
        with self.assertRaises(ValueError):replace(E,original_capture='oops')
    def test_27_bad_int(self):
        with self.assertRaises(ValueError):replace(E,original_value=1.5)
    def test_28_bad_flag(self):
        with self.assertRaises(ValueError):replace(E,same_selection=1)
    def test_29_deterministic(self):self.assertEqual(fixture()[1],fixture()[1])
    def test_30_digest_length(self):self.assertEqual(len(fixture()[1]['result_digest']),64)
    def test_31_frozen(self):self.assertEqual(fixture()[1]['active_parent'],'FROZEN')
    def test_32_no_learning(self):self.assertFalse(fixture()[1]['learning_applied'])
    def test_33_no_witness_claim(self):self.assertFalse(fixture()[1]['witness_independence_verified'])
    def test_34_ledger(self):self.assertEqual(fixture()[0].verify_ledger(),'VALID_LOCAL_CHAIN')
    def test_35_ledger_tamper(self):
        a,_=fixture();a.events[0]['kind']='FORGED';self.assertEqual(a.verify_ledger(),'LEDGER_TAMPERED')
    def test_36_external_rollback(self):self.assertEqual(fixture()[0].verify_ledger('1'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_37_event_sequence(self):
        a,_=fixture();self.assertEqual([x['seq'] for x in a.events],list(range(len(a.events))))
    def test_38_no_mutate_evidence(self):
        before=E.packet();Audit(E,P1,P2).run();self.assertEqual(E.packet(),before)
    def test_39_no_mutate_policy(self):
        before=P1.packet();Audit(E,P1,P2).run();self.assertEqual(P1.packet(),before)
    def test_40_provenance(self):self.assertEqual(evaluate(E,P1)['evidence_digest'],digest(E.packet()))
    def test_41_policy_digest(self):self.assertEqual(evaluate(E,P1)['policy_digest'],digest(P1.packet()))
    def test_42_changed_result_without_changed_evidence(self):
        r=Audit(replace(E,same_question=False),replace(P1,version='v0',require_question_match=False),P1).run()
        self.assertTrue(r['verdict_changed']);self.assertEqual(r['old']['evidence_digest'],r['new']['evidence_digest'])
    def test_43_stable_rejected(self):self.assertEqual(Audit(E,P2,Policy('v4',1)).run()['status'],'POLICY_CHANGED_VERDICT_STABLE')
    def test_44_ledger_records_both(self):
        a,_=fixture();self.assertEqual(len([x for x in a.events if x['kind']=='VERDICT']),2)
    def test_45_hash_chain_truncation_caveat(self):
        a,_=fixture();head=a.events[-1]['hash'];a.events.pop();self.assertEqual(a.verify_ledger(),'VALID_LOCAL_CHAIN');self.assertEqual(a.verify_ledger(head),'EXTERNAL_HEAD_MISMATCH')

if __name__=='__main__':unittest.main(verbosity=2)