import os
import sqlite3
import tempfile
import unittest
from auxiliary import FLAY206,Query,Fact,fixture

class TestAuxiliary(unittest.TestCase):
    def setUp(self):
        self.f=FLAY206(4)
    def tearDown(self):
        self.f.close()
    def scaffold(self):
        for mask in ((1,1,0,0),(0,1,1,0),(0,0,1,1)):
            self.assertEqual(self.f.add_query(Query(mask,1))['action'],'QUERY_RETAINED')
    def test_01_empty(self): self.assertEqual(len(self.f.candidates()),16)
    def test_02_scaffold(self): self.scaffold();self.assertEqual(len(self.f.candidates()),2)
    def test_03_aux_completes(self): self.scaffold();self.assertEqual(self.f.analyze_auxiliary(Fact(0,1,'r','s'))['action'],'AUXILIARY_COMPLETES_RECONSTRUCTION')
    def test_04_no_commit_on_risk(self): self.scaffold();self.f.analyze_auxiliary(Fact(0,1,'r','s'));self.assertEqual(len(self.f.candidates()),2)
    def test_05_risk_allow(self): self.scaffold();self.f.analyze_auxiliary(Fact(0,1,'r','s'),True);self.assertEqual(len(self.f.candidates()),1)
    def test_06_reconstruct_no_extra_query(self): self.scaffold();self.assertEqual(len(self.f.queries),3)
    def test_07_reconstruct_candidate_digest(self): self.scaffold();self.assertEqual(len(self.f.analyze_auxiliary(Fact(0,1,'r','s'))['candidate_digest']),64)
    def test_08_no_change_to_parent(self): self.assertFalse(fixture()['parent_activated'])
    def test_09_chain(self): self.scaffold();self.assertTrue(self.f.verify_chain())
    def test_10_bad_mask(self):
        with self.assertRaises(ValueError): Query((1,2),1)
    def test_11_bad_sum(self):
        with self.assertRaises(ValueError): Query((1,1),3)
    def test_12_negative_sum(self):
        with self.assertRaises(ValueError): Query((1,1),-1)
    def test_13_empty_mask(self):
        with self.assertRaises(ValueError): Query((),0)
    def test_14_bad_q_length(self):
        with self.assertRaises(ValueError): self.f.add_query(Query((1,0),1))
    def test_15_bad_index(self):
        with self.assertRaises(ValueError): self.f.analyze_auxiliary(Fact(4,1,'r','s'))
    def test_16_negative_index(self):
        with self.assertRaises(ValueError): Fact(-1,0,'r','s')
    def test_17_bad_fact_value(self):
        with self.assertRaises(ValueError): Fact(1,2,'r','s')
    def test_18_no_root(self):
        with self.assertRaises(ValueError): Fact(1,0,'','s')
    def test_19_no_source(self):
        with self.assertRaises(ValueError): Fact(1,0,'r','')
    def test_20_dimension_zero(self):
        with self.assertRaises(ValueError): FLAY206(0)
    def test_21_dimension_limit(self):
        with self.assertRaises(ValueError): FLAY206(19)
    def test_22_bool_dim(self):
        with self.assertRaises(ValueError): FLAY206(True)
    def test_23_bool_sum(self):
        with self.assertRaises(ValueError): Query((1,0),True)
    def test_24_bool_fact(self):
        with self.assertRaises(ValueError): Fact(0,True,'r','s')
    def test_25_query_contradiction(self):
        self.f.add_query(Query((1,0,0,0),0),True);self.assertEqual(self.f.add_query(Query((1,0,0,0),1))['action'],'REJECT_CONTRADICTORY_QUERY')
    def test_26_query_atomic(self):
        self.f.add_query(Query((1,0,0,0),0),True);self.f.add_query(Query((1,0,0,0),1));self.assertEqual(len(self.f.queries),1)
    def test_27_aux_contradiction(self):
        self.f.add_query(Query((1,0,0,0),0),True);self.assertEqual(self.f.analyze_auxiliary(Fact(0,1,'r','s'))['action'],'AUXILIARY_CONTRADICTS_OBSERVATIONS')
    def test_28_aux_duplicate(self):
        fact=Fact(0,0,'r','s');self.f.analyze_auxiliary(fact);self.assertEqual(self.f.analyze_auxiliary(fact)['action'],'AUXILIARY_DUPLICATE')
    def test_29_distinct_roots_not_proof(self):
        self.f.analyze_auxiliary(Fact(0,0,'a','x'));self.assertEqual(self.f.analyze_auxiliary(Fact(1,1,'b','y'))['limitations'].startswith('Enumerated'),True)
    def test_30_low_rank_individual_gate(self):
        self.assertEqual(self.f.add_query(Query((1,0,0,0),1))['action'],'BLOCK_INDIVIDUAL_DISCLOSURE')
    def test_31_low_rank_allow(self):
        self.assertEqual(self.f.add_query(Query((1,0,0,0),1),True)['action'],'QUERY_RETAINED')
    def test_32_chain_tamper(self):
        self.f.add_query(Query((1,1,1,1),2));self.f.db.execute("UPDATE audit SET event='{}'");self.f.db.commit();self.assertFalse(self.f.verify_chain())
    def test_33_chain_tamper_hash(self):
        self.f.add_query(Query((1,1,1,1),2));self.f.db.execute("UPDATE audit SET hash='fake'");self.f.db.commit();self.assertFalse(self.f.verify_chain())
    def test_34_unknown_model_after_risk(self): self.scaffold();self.assertEqual(len(self.f.candidates()),2)
    def test_35_fixture(self): self.assertEqual(fixture()['auxiliary_result']['before'],2)
    def test_36_fixture_fixed(self): self.assertEqual(fixture()['auxiliary_result']['after'],1)
    def test_37_fixture_chain(self): self.assertTrue(fixture()['audit_integrity'])
    def test_38_empty_fact_roots(self): self.assertEqual(self.f._report([],[], 'X')['ancestry_roots'],[])
    def test_39_rejected_no_chain(self): self.scaffold();n=self.f.db.execute('SELECT COUNT(*) FROM audit').fetchone()[0];self.f.analyze_auxiliary(Fact(0,1,'r','s'));self.assertEqual(n,self.f.db.execute('SELECT COUNT(*) FROM audit').fetchone()[0])
    def test_40_persistent_chain(self):
        with tempfile.TemporaryDirectory() as td:
            db=os.path.join(td,'audit.sqlite');a=FLAY206(4,db);a.add_query(Query((1,1,1,1),2));a.close();b=FLAY206(4,db);self.assertTrue(b.verify_chain());b.close()

if __name__=='__main__': unittest.main()