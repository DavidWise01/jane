import os
import tempfile
import unittest
from scheduler import Observer, Contract, demonstration

class TestFairness(unittest.TestCase):
    def setUp(self): self.o=Observer(contract=Contract(3))
    def tearDown(self): self.o.close()
    def record(self, chosen, enabled=('A','B'), start=0):
        for i,c in enumerate(chosen): self.o.record(i+start,enabled,c)
    def test_breach(self): self.record(['A','A','A']);self.assertEqual(self.o.evaluate()['status'],'BOUNDED_FAIRNESS_BREACH')
    def test_breach_agent(self): self.record(['A','A','A']);self.assertEqual(self.o.evaluate()['violations'][0]['agent'],'B')
    def test_breach_tick(self): self.record(['A','A','A']);self.assertEqual(self.o.evaluate()['violations'][0]['deadline_tick'],2)
    def test_no_breach(self): self.record(['A','A','B']);self.assertEqual(self.o.evaluate()['status'],'OBSERVED_WITHIN_BUDGET')
    def test_no_observations(self): self.assertEqual(self.o.evaluate()['status'],'NO_OBSERVATIONS')
    def test_demo(self): self.assertEqual(demonstration()['status'],'BOUNDED_FAIRNESS_BREACH')
    def test_demo_no_learning(self): self.assertFalse(demonstration()['learning_applied'])
    def test_demo_no_witness(self): self.assertEqual(demonstration()['independent_witness_increment'],0)
    def test_preserve_parent(self): self.assertEqual(demonstration()['active'],'frozen_parent')
    def test_hash_chain(self): self.record(['A','B']);self.assertEqual(self.o.audit(),'VALID_LOCAL_CHAIN')
    def test_external_head(self): self.record(['A']);self.assertEqual(self.o.audit('f'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_external_good_head(self): h=self.o.record(0,['A'],'A');self.assertEqual(self.o.audit(h),'VALID_LOCAL_CHAIN')
    def test_tamper(self): self.o.record(0,['A'],'A');self.o.db.execute('UPDATE observations SET payload=? WHERE seq=0',('"fake"',));self.o.db.commit();self.assertEqual(self.o.audit(),'TAMPERED')
    def test_audit_blocks_evaluation(self): self.o.record(0,['A'],'A');self.assertEqual(self.o.evaluate('f'*64)['status'],'AUDIT_FAILURE')
    def test_disabled_resets_wait(self): self.o.record(0,['A','B'],'A');self.o.record(1,['A'],'A');self.o.record(2,['A','B'],'A');self.assertEqual(self.o.evaluate()['status'],'OBSERVED_WITHIN_BUDGET')
    def test_service_resets_wait(self): self.record(['A','A','B','A','A']);self.assertEqual(self.o.evaluate()['status'],'OBSERVED_WITHIN_BUDGET')
    def test_chronos_gap(self): self.o.record(0,['A'],'A');self.o.record(2,['A'],'A');self.assertEqual(self.o.evaluate()['status'],'INCONCLUSIVE_OBSERVATION_GAP')
    def test_unknown_tick(self): self.o.record(0,['A'],'A');self.o.record(1,[],observed=False);self.o.record(2,['A'],'A');self.assertEqual(self.o.evaluate()['status'],'INCONCLUSIVE_OBSERVATION_GAP')
    def test_gap_no_false_breach(self): self.o.record(0,['A','B'],'A');self.o.record(4,['A','B'],'A');self.assertEqual(self.o.evaluate()['violations'],[])
    def test_unknown_no_false_breach(self): self.o.record(0,['A','B'],'A');self.o.record(1,[],observed=False);self.o.record(2,['A','B'],'A');self.assertEqual(self.o.evaluate()['violations'],[])
    def test_contract_limit(self):
        for v in (0,10001,1.5,True,-1):
            with self.subTest(v=v),self.assertRaises(ValueError):Contract(v)
    def test_invalid_stamp(self):
        for v in (-1,'0',None,True):
            with self.subTest(v=v),self.assertRaises(ValueError):self.o.record(v,['A'],'A')
    def test_duplicate_stamp(self): self.o.record(0,['A'],'A');self.assertRaises(ValueError,self.o.record,0,['A'],'A')
    def test_reverse_stamp(self): self.o.record(2,['A'],'A');self.assertRaises(ValueError,self.o.record,1,['A'],'A')
    def test_non_enabled_choice(self): self.assertRaises(ValueError,self.o.record,0,['A'],'B')
    def test_empty_agent(self): self.assertRaises(ValueError,self.o.record,0,[''],'')
    def test_duplicate_agent(self): self.assertRaises(ValueError,self.o.record,0,['A','A'],'A')
    def test_too_many_agents(self): self.assertRaises(ValueError,self.o.record,0,[str(i) for i in range(129)],'0')
    def test_unknown_must_not_claim_choice(self): self.assertRaises(ValueError,self.o.record,0,['A'],'A',False)
    def test_empty_enabled_no_selection(self): self.o.record(0,[]);self.assertEqual(self.o.evaluate()['status'],'OBSERVED_WITHIN_BUDGET')
    def test_deadline_one(self):
        o=Observer(contract=Contract(1));o.record(0,['A','B'],'A');self.assertEqual(o.evaluate()['status'],'BOUNDED_FAIRNESS_BREACH');o.close()
    def test_no_op_counts_as_unserved(self): self.record([None,None,None]);self.assertEqual(self.o.evaluate()['status'],'BOUNDED_FAIRNESS_BREACH')
    def test_reproducible(self): self.assertEqual(demonstration()['digest'],demonstration()['digest'])
    def test_coverage_count(self): self.record(['A','B']);self.assertEqual(len(self.o.evaluate()['coverage']),2)
    def test_scope(self): self.assertIn('finite observed',demonstration()['scope'])
    def test_stale_head_after_append(self): h=self.o.record(0,['A'],'A');self.o.record(1,['A'],'A');self.assertEqual(self.o.audit(h),'EXTERNAL_HEAD_MISMATCH')
    def test_restart_sqlite(self):
        with tempfile.TemporaryDirectory() as d:
            p=os.path.join(d,'obs.db');x=Observer(p,Contract(3));x.record(0,['A','B'],'A');x.close();y=Observer(p,Contract(3));y.record(1,['A','B'],'A');y.record(2,['A','B'],'A');self.assertEqual(y.evaluate()['status'],'BOUNDED_FAIRNESS_BREACH');y.close()
    def test_gap_must_reset_streak(self):
        self.o.record(0,['A','B'],'A');self.o.record(1,['A','B'],'A')
        self.o.record(4,['A','B'],'A')
        self.assertEqual(self.o.evaluate()['violations'],[])
    def test_gap_followed_by_real_breach(self):
        self.o.record(0,['A','B'],'A');self.o.record(3,['A','B'],'A')
        self.o.record(4,['A','B'],'A');self.o.record(5,['A','B'],'A')
        self.assertEqual(self.o.evaluate()['status'],'BOUNDED_FAIRNESS_BREACH')
    def test_non_boolean_observed(self): self.assertRaises(ValueError,self.o.record,0,['A'],None,1)
    def test_short_window(self):self.record(['A','A']);self.assertEqual(self.o.evaluate()['status'],'OBSERVED_WITHIN_BUDGET')
    def test_multi_agent(self): self.o.record(0,['A','B','C'],'A');self.o.record(1,['A','B','C'],'B');self.o.record(2,['A','B','C'],'C');self.assertEqual(self.o.evaluate()['status'],'OBSERVED_WITHIN_BUDGET')
if __name__=='__main__':unittest.main()