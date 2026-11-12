import unittest
from dataclasses import replace
from cohort import Case,Flay140,demo,root_of

def make(i,cohort='A',baseline=False,candidate=True,truth=True,split='holdout',surface='internet',ancestry='external:A'):
    return Case(str(i),cohort,ancestry,truth,baseline,candidate,split,surface,f'{i+100:064x}')

class CohortTests(unittest.TestCase):
    def test_demo_eight(self): self.assertEqual(demo()[1]['n'],8)
    def test_aggregate_gain(self): self.assertEqual(demo()[1]['candidate_correct'],6)
    def test_parent_correct(self): self.assertEqual(demo()[1]['baseline_correct'],2)
    def test_subgroup_veto(self): self.assertEqual(demo()[1]['status'],'BLOCK_SUBGROUP_REGRESSION')
    def test_gross_gain(self): self.assertEqual(demo()[1]['gross_gain'],6)
    def test_gross_regression(self): self.assertEqual(demo()[1]['gross_regression'],2)
    def test_veto_group_b(self): self.assertEqual(demo()[1]['cohorts'][1]['status'],'REGRESSION')
    def test_no_activation(self): self.assertEqual(demo()[1]['active'],'frozen_parent')
    def test_no_learning(self): self.assertFalse(demo()[1]['learning_applied'])
    def test_ledger(self): self.assertEqual(demo()[0].audit(),'VALID_LOCAL_CHAIN')
    def test_deterministic(self): self.assertEqual(demo()[1],demo()[1])
    def test_mirror_root(self): self.assertEqual(root_of('github','x'),root_of('0root.ai','y'))
    def test_external_root(self): self.assertEqual(root_of('internet','other'),'other')
    def test_case_duplicate(self):
        with self.assertRaises(ValueError): Flay140().evaluate([make(1),make(1)])
    def test_bad_split(self):
        with self.assertRaises(ValueError): Flay140().evaluate([make(1,split='train')])
    def test_empty(self):
        with self.assertRaises(ValueError): Flay140().evaluate([])
    def test_missing_ancestry(self):
        with self.assertRaises(ValueError): Flay140().evaluate([make(1,ancestry='')])
    def test_holdout_leak(self):
        c=make(1)
        self.assertEqual(Flay140().evaluate([c],known_training_hashes=[c.content_hash])['status'],'HOLDOUT_LEAKAGE')
    def test_leak_retained_in_log(self):
        f=Flay140();c=make(1);f.evaluate([c],known_training_hashes=[c.content_hash]);self.assertEqual(f.events[0]['kind'],'QUARANTINE')
    def test_small_cohort(self): self.assertEqual(Flay140().evaluate([make(1)])['status'],'ABSTAIN_SMALL_COHORT')
    def test_abstention(self):
        cs=[make(1,candidate=None),make(2)]
        self.assertEqual(Flay140().evaluate(cs)['status'],'ABSTAIN_INCOMPLETE_COVERAGE')
    def test_clean_review(self):
        cs=[make(1),make(2)]
        self.assertEqual(Flay140().evaluate(cs)['status'],'JANE_REVIEW_CANDIDATE')
    def test_no_improvement(self):
        cs=[make(1,baseline=True),make(2,baseline=True)]
        self.assertEqual(Flay140().evaluate(cs)['status'],'NO_IMPROVEMENT')
    def test_audit_tamper(self):
        f,_=demo();f.events[0]['kind']='ALTERED';self.assertEqual(f.audit(),'TAMPERED')
    def test_limit(self):
        with self.assertRaises(ValueError): Flay140().evaluate([make(i) for i in range(257)])
    def test_min_cohort_limit(self):
        with self.assertRaises(ValueError): Flay140().evaluate([make(1)],min_cohort=0)
    def test_cohort_count(self): self.assertEqual(len(demo()[1]['cohorts']),2)
    def test_source_root_no_fake_increment(self): self.assertEqual(demo()[1]['cohorts'][0]['distinct_roots'],1)
    def test_valid_boolean(self):
        with self.assertRaises(ValueError):Flay140().evaluate([replace(make(1),candidate='yes')])
    def test_digest_present(self):self.assertEqual(len(demo()[1]['digest']),64)

if __name__=='__main__':unittest.main(verbosity=2)
