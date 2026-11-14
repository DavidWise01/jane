import unittest
from dataclasses import replace
from selection import Round, audit, demo, digest

def make(n=8, selected=None, status='published', ancestry='root'):
    if selected is None:selected=set(range(n))
    return [Round(i,'day' if i<n//2 else 'night',i in selected,'obs'+str(i), ancestry+str(i),status if i in selected else 'unselected') for i in range(n)]
class Tests(unittest.TestCase):
    def test_demo(self):self.assertEqual(demo()['status'],'SELECTION_COVERAGE_IMBALANCE')
    def test_demo_population(self):self.assertEqual(demo()['population_rounds'],16)
    def test_demo_selected(self):self.assertEqual(demo()['selected_rounds'],8)
    def test_demo_day(self):self.assertEqual(demo()['by_band']['day']['selected'],6)
    def test_demo_night(self):self.assertEqual(demo()['by_band']['night']['selected'],2)
    def test_demo_unequal(self):self.assertTrue(demo()['unequal_selection_rates'])
    def test_demo_bounds(self):self.assertEqual(demo()['population_published_fraction_bounds'],[5/16,13/16])
    def test_demo_no_causality(self):self.assertFalse(demo()['causal_claim'])
    def test_demo_no_independence(self):self.assertFalse(demo()['independence_established'])
    def test_balanced(self):self.assertEqual(audit(make())['status'],'COVERAGE_BALANCED_FIXTURE')
    def test_uncovered(self):self.assertEqual(audit(make(selected={0,1}))['status'],'UNCOVERED_POPULATION_STRATUM')
    def test_uncovered_night(self):self.assertEqual(audit(make(selected={0}))['uncovered_bands'],['night'])
    def test_shared_ancestry(self):self.assertEqual(audit(make(ancestry='same') if False else [replace(r,ancestry='same') for r in make()])['status'],'SHARED_OBSERVER_ANCESTRY')
    def test_unknown_bound(self):self.assertEqual(audit(make(selected={0}))['population_published_fraction_bounds'],[1/8,1])
    def test_all_known(self):self.assertEqual(audit(make())['population_published_fraction_bounds'],[1,1])
    def test_all_missing(self):self.assertEqual(audit(make(status='not_observed'))['population_published_fraction_bounds'],[0,0])
    def test_outage_unknown(self):self.assertEqual(audit(make(status='outage'))['population_published_fraction_bounds'],[0,1])
    def test_empty(self):
        with self.assertRaises(ValueError):audit([])
    def test_duplicate(self):
        with self.assertRaises(ValueError):audit([make()[0],make()[0]])
    def test_population_gap(self):
        with self.assertRaises(ValueError):audit([make()[0],make()[2]])
    def test_limit(self):
        with self.assertRaises(ValueError):audit(make(8),max_rounds=4)
    def test_negative_index(self):
        with self.assertRaises(ValueError):Round(-1,'day',True,'o','a','published')
    def test_bad_band(self):
        with self.assertRaises(ValueError):Round(0,'sunset',True,'o','a','published')
    def test_bad_status(self):
        with self.assertRaises(ValueError):Round(0,'day',True,'o','a','missing')
    def test_unselected_claim(self):
        with self.assertRaises(ValueError):Round(0,'day',False,'o','a','published')
    def test_selected_unselected(self):
        with self.assertRaises(ValueError):Round(0,'day',True,'o','a','unselected')
    def test_missing_observer(self):
        with self.assertRaises(ValueError):Round(0,'day',True,'','a','published')
    def test_missing_root(self):
        with self.assertRaises(ValueError):Round(0,'day',True,'o','','published')
    def test_bool_index(self):
        with self.assertRaises(ValueError):Round(True,'day',True,'o','a','published')
    def test_bool_selected(self):
        with self.assertRaises(ValueError):Round(0,'day',1,'o','a','published')
    def test_order_independent(self):self.assertEqual(audit(make()),audit(list(reversed(make()))))
    def test_digest_repeatable(self):self.assertEqual(demo()['digest'],demo()['digest'])
    def test_digest_different_selection(self):self.assertNotEqual(audit(make())['policy_digest'],audit(make(selected={0}))['policy_digest'])
    def test_outage_band(self):self.assertEqual(audit(make(status='outage'))['by_band']['day']['outages'],4)
    def test_root_count(self):self.assertEqual(audit(make())['declared_observation_roots'],8)
    def test_observer_count(self):self.assertEqual(audit(make())['selected_observers'],8)
    def test_parent(self):self.assertEqual(demo()['active_parent'],'frozen')
    def test_status_stability(self):self.assertEqual(demo()['status'],demo()['status'])
    def test_digest_length(self):self.assertEqual(len(digest(demo())),64)
    def test_band_coverage(self):self.assertEqual(demo()['by_band']['night']['coverage'],.25)
    def test_publication_coverage(self):self.assertEqual(demo()['by_band']['day']['published'],4)
    def test_missing_count(self):self.assertEqual(demo()['by_band']['night']['not_observed'],1)
if __name__=='__main__':unittest.main(verbosity=2)