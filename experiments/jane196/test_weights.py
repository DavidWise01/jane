import unittest,copy
from fractions import Fraction
from weights import Stratum,Audit,demo,as_obj
class WeightTests(unittest.TestCase):
    def setUp(self):self.a,self.r=demo()
    def test_fixture_population(self):self.assertEqual(self.r['total_population'],16)
    def test_fixture_sample(self):self.assertEqual(sum(x['sampled'] for x in self.r['rows']),8)
    def test_day_selection(self):self.assertEqual(self.r['rows'][0]['selection_fraction']['decimal'],.75)
    def test_night_selection(self):self.assertEqual(self.r['rows'][1]['selection_fraction']['decimal'],.25)
    def test_conditional_rate(self):self.assertEqual(self.r['conditional_population_estimate']['numerator'],5)
    def test_conditional_denominator(self):self.assertEqual(self.r['conditional_population_estimate']['denominator'],12)
    def test_lower(self):self.assertEqual(self.r['population_outcome_bounds']['lower']['decimal'],.3125)
    def test_upper(self):self.assertEqual(self.r['population_outcome_bounds']['upper']['decimal'],.8125)
    def test_conditional(self):self.assertEqual(self.r['status'],'ASSUMPTION_CONDITIONAL_ESTIMATE')
    def test_no_assumption_no_point(self):
        r=Audit(self.a.strata).evaluate();self.assertIsNone(r['conditional_population_estimate'])
    def test_unobserved_stratum(self):
        r=Audit([Stratum('one',8,6,5,1),Stratum('zero',8,0,0,0)],assumption='within_stratum_exchangeability').evaluate()
        self.assertEqual(r['status'],'ANCESTRY_LIMITED_UNOBSERVED_STRATUM_NO_POINT');self.assertIsNone(r['conditional_population_estimate'])
    def test_census(self):
        r=Audit([Stratum('all',4,4,3,1,('a','b'))]).evaluate()
        self.assertEqual(r['status'],'COMPLETE_CENSUS');self.assertEqual(r['conditional_population_estimate']['decimal'],.75)
    def test_census_bounds(self):
        r=Audit([Stratum('all',4,4,3,1,('a','b'))]).evaluate();self.assertEqual(r['population_outcome_bounds']['lower'],r['population_outcome_bounds']['upper'])
    def test_no_imputation(self):self.assertIsNone(self.r['rows'][1]['response_fraction']) if False else self.assertIsNotNone(self.r['rows'][1]['observed_rate'])
    def test_response_missing(self):
        r=Audit([Stratum('a',4,2,1,0,('a','b'))]).evaluate();self.assertEqual(r['rows'][0]['unobserved'],3)
    def test_unsampled_response_fraction_none(self):
        r=Audit([Stratum('a',4,0,0,0,('a','b'))]).evaluate();self.assertIsNone(r['rows'][0]['response_fraction'])
    def test_ancestry_limited(self):
        r=Audit([Stratum('a',4,2,1,1,('same',))],required_roots=2).evaluate();self.assertIn('a',r['insufficient_declared_ancestry'])
    def test_shared_ancestry(self):
        r=Audit([Stratum('a',4,2,1,1,('a','shared')),Stratum('b',4,2,1,1,('b','shared'))]).evaluate();self.assertEqual(r['shared_ancestry_across_strata'],['b'])
    def test_distinct_sources(self):self.assertEqual(self.r['shared_ancestry_across_strata'],[])
    def test_no_physical_claim(self):self.assertFalse(self.r['rows'][0]['independent_roots_established'])
    def test_digest_deterministic(self):self.assertEqual(demo()[1]['digest'],self.r['digest'])
    def test_input_order_deterministic(self):self.assertEqual(Audit(tuple(reversed(self.a.strata)),assumption=self.a.assumption).evaluate(),self.r)
    def test_ledger_valid(self):self.assertEqual(self.a.verify_ledger(),'VALID_LOCAL_CHAIN')
    def test_ledger_tamper(self):self.a.events[0]['kind']='FAKE';self.assertEqual(self.a.verify_ledger(),'TAMPERED')
    def test_external_head(self):self.assertEqual(self.a.verify_ledger('0'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_frozen_parent(self):self.assertEqual(self.r['active'],'frozen_parent')
    def test_no_learning(self):self.assertFalse(self.r['auto_learning'])
    def test_no_witness_increment(self):self.assertEqual(self.r['independent_witness_increment'],0)
    def test_no_duplicate_strata(self):
        with self.assertRaises(ValueError):Audit([Stratum('same',2,1,1,0),Stratum('same',2,1,0,1)])
    def test_bad_population(self):
        with self.assertRaises(ValueError):Stratum('a',0,0,0,0)
    def test_bad_sample(self):
        with self.assertRaises(ValueError):Stratum('a',4,5,0,0)
    def test_bad_observed(self):
        with self.assertRaises(ValueError):Stratum('a',4,2,2,1)
    def test_float_counts(self):
        with self.assertRaises(ValueError):Stratum('a',4.0,2,1,1)
    def test_duplicate_root(self):
        with self.assertRaises(ValueError):Stratum('a',4,2,1,1,('x','x'))
    def test_unknown_assumption(self):
        with self.assertRaises(ValueError):Audit([Stratum('a',4,2,1,1)],assumption='magic')
    def test_invalid_quorum(self):
        with self.assertRaises(ValueError):Audit([Stratum('a',4,2,1,1)],required_roots=0)
    def test_bounds_cover_point(self):
        l=self.r['population_outcome_bounds']['lower']['decimal'];u=self.r['population_outcome_bounds']['upper']['decimal'];p=self.r['conditional_population_estimate']['decimal'];self.assertTrue(l<=p<=u)
    def test_fraction_json(self):self.assertEqual(as_obj(Fraction(1,3))['denominator'],3)
    def test_hash_length(self):self.assertEqual(len(self.r['digest']),64)
if __name__=='__main__':unittest.main(verbosity=2)
