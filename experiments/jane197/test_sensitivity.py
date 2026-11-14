import unittest
from fractions import Fraction as F
from sensitivity import Stratum,Assumption,Audit,demo

class TestMNAR(unittest.TestCase):
    def setUp(self):self.s=[Stratum('day',8,6,5,'A'),Stratum('night',8,2,0,'B')]
    def audit(self):return Audit(self.s)
    def run_delta(self,d):return self.audit().evaluate(Assumption('scenario',(F(d),F(d))))
    def test_frozen(self):self.assertEqual(self.audit().parent,'frozen')
    def test_population(self):self.assertEqual(self.audit().population,16)
    def test_observed(self):self.assertEqual(sum(x.observed for x in self.s),8)
    def test_missing(self):self.assertEqual(self.audit().bounds()['missing'],8)
    def test_min(self):self.assertEqual(self.audit().bounds()['lower']['percentage'],31.25)
    def test_max(self):self.assertEqual(self.audit().bounds()['upper']['percentage'],81.25)
    def test_equal(self):self.assertAlmostEqual(self.run_delta(0)['estimate']['percentage'],41.666667,places=5)
    def test_negative(self):self.assertLess(self.run_delta(F(-1,4))['estimate']['percentage'],self.run_delta(0)['estimate']['percentage'])
    def test_positive(self):self.assertGreater(self.run_delta(F(1,4))['estimate']['percentage'],self.run_delta(0)['estimate']['percentage'])
    def test_extreme_low(self):self.assertEqual(self.run_delta(-1)['estimate']['percentage'],31.25)
    def test_extreme_high(self):self.assertEqual(self.run_delta(1)['estimate']['percentage'],81.25)
    def test_clip_upper(self):self.assertEqual(self.run_delta(1)['strata'][0]['assumed_missing_rate']['percentage'],100)
    def test_clip_lower(self):self.assertEqual(self.run_delta(-1)['strata'][0]['assumed_missing_rate']['percentage'],0)
    def test_unknown_stratum(self):
        a=Audit([Stratum('empty',8,0,0,'A')]);r=a.evaluate(Assumption('no-data',(F(0),)))
        self.assertEqual(r['status'],'UNIDENTIFIED_STRATUM');self.assertIsNone(r['estimate'])
    def test_unknown_bounds(self):
        a=Audit([Stratum('empty',8,0,0,'A')]);self.assertEqual(a.bounds()['upper']['percentage'],100)
    def test_all_observed(self):
        a=Audit([Stratum('all',10,10,6,'A')]);self.assertEqual(a.evaluate(Assumption('fixed',(F(1),)))['estimate']['percentage'],60)
    def test_no_imputation_into_data(self):
        a=self.audit();a.evaluate(Assumption('x',(F(1),F(1))))
        self.assertEqual(a.strata,tuple(self.s))
    def test_frozen_digest_same(self):self.assertEqual(self.audit().frozen_digest,self.audit().frozen_digest)
    def test_digest_across_scenarios(self):self.assertEqual(self.run_delta(0)['evidence_digest'],self.run_delta(1)['evidence_digest'])
    def test_estimate_changes(self):self.assertNotEqual(self.run_delta(0)['digest'],self.run_delta(1)['digest'])
    def test_provenance_duplicate(self):
        a=Audit([Stratum('a',8,6,5,'same'),Stratum('b',8,2,0,'same')]);self.assertTrue(a.ancestry_warning)
    def test_independent_not_derived(self):self.assertEqual(self.run_delta(0)['independent_witness_increment'],0)
    def test_no_learning(self):self.assertFalse(self.run_delta(0)['learning_applied'])
    def test_bad_stratum_counts(self):
        with self.assertRaises(ValueError):Stratum('x',8,9,2,'r')
    def test_bad_successes(self):
        with self.assertRaises(ValueError):Stratum('x',8,2,3,'r')
    def test_bad_types(self):
        with self.assertRaises(ValueError):Stratum('x',8,2.0,1,'r')
    def test_bad_population(self):
        with self.assertRaises(ValueError):Stratum('x',0,0,0,'r')
    def test_bad_ancestry(self):
        with self.assertRaises(ValueError):Stratum('x',8,2,1,'')
    def test_duplicate_name(self):
        with self.assertRaises(ValueError):Audit([self.s[0],self.s[0]])
    def test_empty_population(self):
        with self.assertRaises(ValueError):Audit([])
    def test_malformed_delta(self):
        with self.assertRaises(ValueError):Assumption('bad',(0,0))
    def test_delta_overflow(self):
        with self.assertRaises(ValueError):Assumption('bad',(F(2),))
    def test_mismatched_delta(self):
        with self.assertRaises(ValueError):self.audit().evaluate(Assumption('bad',(F(0),)))
    def test_hash_chain(self):self.assertEqual(demo()[0].audit_chain(),'VALID_LOCAL_CHAIN')
    def test_external_head(self):self.assertEqual(demo()[0].audit_chain('0'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_mutate_event(self):
        a=self.audit();a.events[0]['kind']='tamper';self.assertEqual(a.audit_chain(),'TAMPERED')
    def test_deterministic(self):self.assertEqual(demo()[1],demo()[1])
    def test_scenario_count(self):self.assertEqual(len(demo()[1]['scenarios']),5)
    def test_no_probabilistic_certainty(self):self.assertIn('not observed truth',self.run_delta(0)['inference_scope'])
    def test_other_strata_names(self):self.assertEqual(self.run_delta(0)['strata'][1]['name'],'night')
    def test_zero_missing_nostrata(self):
        a=Audit([Stratum('all',10,10,6,'A')]);self.assertEqual(a.bounds()['lower'],a.bounds()['upper'])
if __name__=='__main__':unittest.main(verbosity=2)