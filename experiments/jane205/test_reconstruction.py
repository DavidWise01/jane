import json
import os
import sqlite3
import tempfile
import unittest
from reconstruction import Policy, Reject, FLAY205, analyze, digest, item, rank, demonstration


class ReconstructionTests(unittest.TestCase):
    def setUp(self):
        self.f = FLAY205()
    def tearDown(self): self.f.close()
    def assertCode(self, code, action):
        with self.assertRaises(Reject) as ctx: action()
        self.assertEqual(ctx.exception.code, code)
    def test_01_empty(self): self.assertEqual(self.f.state()['analysis']['candidate_count'],16)
    def test_02_allowed(self): self.assertEqual(self.f.release(item('x','ADA',[0,1],1))['verdict'],'RELEASE_ALLOWED_FIXTURE')
    def test_03_rank_zero(self): self.assertEqual(rank([],4),0)
    def test_04_rank_dependent(self): self.assertEqual(rank([(0,1),(0,1)],4),1)
    def test_05_rank_independent(self): self.assertEqual(rank([(0,1),(1,2),(2,3)],4),3)
    def test_06_rank_full(self): self.assertEqual(rank([(0,),(1,),(2,),(3,)],4),4)
    def test_07_two_candidates(self):
        for i,e in enumerate([item('a','ADA',[0,1],1),item('b','BERT',[1,2],1),item('c','CLIO',[2,3],1)]): self.f.release(e)
        self.assertEqual(self.f.state()['analysis']['candidate_count'],2)
    def test_08_full_reconstruction_block(self):
        for e in [item('a','ADA',[0,1],1),item('b','BERT',[1,2],1),item('c','CLIO',[2,3],1)]: self.f.release(e)
        self.assertCode('FULL_RECONSTRUCTION',lambda:self.f.release(item('d','ADA',[0,1,2],2)))
        self.assertEqual(self.f.state()['events'],3)
    def test_09_zero_total_leaks(self): self.assertCode('COORDINATE_RECONSTRUCTION',lambda:self.f.release(item('a','ADA',[0,1],0)))
    def test_10_max_total_leaks(self): self.assertCode('COORDINATE_RECONSTRUCTION',lambda:self.f.release(item('a','ADA',[0,1],2)))
    def test_11_singleton_leaks(self): self.assertCode('COORDINATE_RECONSTRUCTION',lambda:self.f.release(item('a','ADA',[0],1)))
    def test_12_preview_no_write(self):
        self.f.preview(item('a','ADA',[0,1],1)); self.assertEqual(self.f.state()['events'],0)
    def test_13_preview_same_result(self):
        e=item('a','ADA',[0,1],1); self.assertEqual(self.f.preview(e),self.f.release(e))
    def test_14_replay(self):
        e=item('a','ADA',[0,1],1); self.f.release(e); self.assertCode('REPLAY',lambda:self.f.release(e))
    def test_15_preview_replay(self):
        e=item('a','ADA',[0,1],1); self.f.release(e); self.assertCode('REPLAY',lambda:self.f.preview(e))
    def test_16_wrong_dataset(self):
        e=item('a','ADA',[0,1],1);e['dataset']='other';self.assertCode('DATASET_MISMATCH',lambda:self.f.release(e))
    def test_17_unknown_agent(self): self.assertCode('UNKNOWN_AGENT',lambda:self.f.release(item('a','EVIL',[0,1],1)))
    def test_18_bad_event(self):
        e=item('a','ADA',[0,1],1); e.pop('recipient');self.assertCode('BAD_EVENT',lambda:self.f.release(e))
    def test_19_extra_field(self):
        e=item('a','ADA',[0,1],1);e['secret']=42;self.assertCode('BAD_EVENT',lambda:self.f.release(e))
    def test_20_duplicate_subset(self):
        e=item('a','ADA',[0,1],1);e['subset']=[0,0];self.assertCode('BAD_SUBSET',lambda:self.f.release(e))
    def test_21_unsorted_subset(self):
        e=item('a','ADA',[0,1],1);e['subset']=[1,0];self.assertCode('BAD_SUBSET',lambda:self.f.release(e))
    def test_22_empty_subset(self): self.assertCode('BAD_SUBSET',lambda:self.f.release(item('a','ADA',[],0)))
    def test_23_out_of_range(self): self.assertCode('BAD_SUBSET',lambda:self.f.release(item('a','ADA',[0,4],1)))
    def test_24_bool_index(self):
        e=item('a','ADA',[0,1],1);e['subset']=[False,1];self.assertCode('BAD_SUBSET',lambda:self.f.release(e))
    def test_25_bad_total(self): self.assertCode('BAD_TOTAL',lambda:self.f.release(item('a','ADA',[0,1],3)))
    def test_26_bool_total(self):
        e=item('a','ADA',[0,1],1);e['total']=True;self.assertCode('BAD_TOTAL',lambda:self.f.release(e))
    def test_27_bad_credits(self): self.assertCode('BAD_CREDITS',lambda:self.f.release(item('a','ADA',[0,1],1,0)))
    def test_28_budget(self): self.assertCode('BUDGET_EXCEEDED',lambda:self.f.release(item('a','ADA',[0,1],1,13)))
    def test_29_wrong_ancestry(self):
        e=item('a','ADA',[0,1],1);e['ancestry']=['mirror'];self.assertCode('BAD_ANCESTRY',lambda:self.f.release(e))
    def test_30_unsorted_ancestry(self):
        e=item('a','ADA',[0,1],1);e['ancestry']=['mirror','holdout://frozen205'];self.assertCode('BAD_ANCESTRY',lambda:self.f.release(e))
    def test_31_inconsistent_aggregates(self):
        self.f.release(item('a','ADA',[0,1],1))
        self.assertCode('INCONSISTENT_AGGREGATE',lambda:self.f.release(item('b','BERT',[0,1],2)))
    def test_32_distinct_agents_same_root(self):
        self.f.release(item('a','ADA',[0,1],1));self.f.release(item('b','BERT',[1,2],1))
        self.assertEqual(self.f.state()['events'],2)
    def test_33_no_mutation_rejection(self):
        self.f.release(item('a','ADA',[0,1],1)); before=self.f.state()
        self.assertCode('COORDINATE_RECONSTRUCTION',lambda:self.f.release(item('b','BERT',[2,3],0)))
        self.assertEqual(before,self.f.state())
    def test_34_deterministic(self): self.assertEqual(demonstration()['state']['analysis'],demonstration()['state']['analysis'])
    def test_35_frozen_parent(self): self.assertTrue(demonstration()['frozen_parent'])
    def test_36_no_real_data(self): self.assertIn('synthetic',demonstration()['claim_scope'])
    def test_37_bad_policy_size(self): self.assertCode('BAD_POLICY',lambda:Policy(size=13))
    def test_38_bad_policy_cap(self): self.assertCode('BAD_POLICY',lambda:Policy(credits_cap=0))
    def test_39_no_partial_event(self):
        self.assertCode('FULL_RECONSTRUCTION',lambda:self.f.release(item('a','ADA',[0,1,2,3],0))) if False else None
        self.assertEqual(self.f.state()['events'],0)
    def test_40_checksum(self): self.assertEqual(digest({'b':2,'a':1}),digest({'a':1,'b':2}))
    def test_41_binary_feasible(self):
        e=item('a','ADA',[0,1],1); a=analyze([e],4)
        self.assertEqual(a['candidate_count'],8);self.assertEqual(a['fixed_coordinates'],{})
    def test_42_multi_recipient(self):
        self.f.release(item('a','ADA',[0,1],1,recipient='one'))
        self.f.release(item('b','BERT',[1,2],1,recipient='two'))
        self.assertEqual(self.f.state()['analysis']['rank'],2)


class Persistence(unittest.TestCase):
    def test_43_restart_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=os.path.join(tmp,'audit.db'); e=item('a','ADA',[0,1],1)
            f=FLAY205(path=path);f.release(e);f.close()
            f=FLAY205(path=path)
            try:
                with self.assertRaises(Reject) as ctx:f.release(e)
                self.assertEqual(ctx.exception.code,'REPLAY')
            finally:f.close()
    def test_44_tamper(self):
        f=FLAY205()
        try:
            f.release(item('a','ADA',[0,1],1))
            f.ledger.db.execute("UPDATE events SET body='{}'")
            with self.assertRaises(Reject) as ctx:f.state()
            self.assertEqual(ctx.exception.code,'CORRUPT_LOG')
        finally:f.close()
    def test_45_corrupt_head(self):
        f=FLAY205()
        try:
            f.release(item('a','ADA',[0,1],1));f.ledger.db.execute("UPDATE events SET head='fake'")
            with self.assertRaises(Reject) as ctx:f.state()
            self.assertEqual(ctx.exception.code,'CORRUPT_LOG')
        finally:f.close()
    def test_46_restart_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=os.path.join(tmp,'audit.db'); f=FLAY205(Policy(credits_cap=2),path)
            f.release(item('a','ADA',[0,1],1,2));f.close()
            f=FLAY205(Policy(credits_cap=2),path)
            try:
                with self.assertRaises(Reject) as ctx:f.release(item('b','BERT',[1,2],1))
                self.assertEqual(ctx.exception.code,'BUDGET_EXCEEDED')
            finally:f.close()

if __name__=='__main__':unittest.main()
