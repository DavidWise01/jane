import copy
import unittest
from fractions import Fraction
from drift import audit, fixture, probability, demo, digest

class TestJANE208(unittest.TestCase):
    def run_case(self,mode):return audit(*fixture(mode))
    def test_current(self):
        r=self.run_case('current');self.assertEqual(r['verdict'],'CONDITIONAL_TRANSFER_FIXTURE');self.assertEqual(r['posterior'],{'0101':'2/11','1010':'9/11'})
    def test_stale(self):self.assertEqual(self.run_case('stale')['verdict'],'STALE_CALIBRATION')
    def test_population(self):self.assertEqual(self.run_case('population')['verdict'],'POPULATION_TRANSFER_UNVERIFIED')
    def test_shift(self):self.assertEqual(self.run_case('monitoring-shift')['verdict'],'MONITORING_SHIFT_DETECTED')
    def test_future(self):self.assertEqual(self.run_case('future')['verdict'],'CALIBRATION_FROM_FUTURE')
    def test_small(self):self.assertEqual(self.run_case('small')['verdict'],'INSUFFICIENT_CALIBRATION')
    def test_artifact(self):self.assertEqual(self.run_case('artifact')['verdict'],'ARTIFACT_VERSION_MISMATCH')
    def test_identity(self):self.assertEqual(self.run_case('identity')['verdict'],'CALIBRATION_ID_MISMATCH')
    def test_zero(self):self.assertEqual(self.run_case('zero')['verdict'],'ZERO_LIKELIHOOD_CONFLICT')
    def test_boundary(self):self.assertEqual(self.run_case('boundary')['verdict'],'CONDITIONAL_TRANSFER_FIXTURE')
    def test_no_posterior_on_withheld(self):
        for mode in ('stale','population','monitoring-shift','future','small','artifact','identity','zero'):
            with self.subTest(mode=mode):self.assertIsNone(self.run_case(mode)['posterior'])
    def test_frozen_fixture(self):
        a=fixture(); b=copy.deepcopy(a);audit(*a);self.assertEqual(a,b)
    def test_determinism(self):self.assertEqual(self.run_case('current'),self.run_case('current'))
    def test_policy_tighter(self):self.assertEqual(audit(*fixture(),max_age=5)['verdict'],'STALE_CALIBRATION')
    def test_policy_age_exact(self):self.assertEqual(audit(*fixture(),max_age=10)['verdict'],'CONDITIONAL_TRANSFER_FIXTURE')
    def test_policy_gap_tighter(self):self.assertEqual(audit(*fixture(),max_rate_gap='1/25')['verdict'],'MONITORING_SHIFT_DETECTED')
    def test_policy_gap_equal(self):self.assertEqual(audit(*fixture(),max_rate_gap='1/20')['verdict'],'CONDITIONAL_TRANSFER_FIXTURE')
    def test_min_n(self):self.assertEqual(audit(*fixture(),min_n=121)['verdict'],'INSUFFICIENT_CALIBRATION')
    def test_all_fixture_modes(self):self.assertEqual(len(demo()['fixtures']),10)
    def test_digest_changes(self):
        p,c,d=fixture();before=audit(p,c,d)['evidence_digest'];d['observed_rates']['positive']='3/5';self.assertNotEqual(before,audit(p,c,d)['evidence_digest'])
    def test_reordered_maps_hash_same(self):
        self.assertEqual(digest({'a':1,'b':2}),digest({'b':2,'a':1}))
    def test_wrong_prior_keys(self):
        p,c,d=fixture();p={'1010':'1'}
        with self.assertRaises(ValueError):audit(p,c,d)
    def test_prior_not_sum(self):
        p,c,d=fixture();p['1010']='1/3'
        with self.assertRaises(ValueError):audit(p,c,d)
    def test_negative_prob(self):
        with self.assertRaises(ValueError):probability('-1/3')
    def test_gt_one_prob(self):
        with self.assertRaises(ValueError):probability('4/3')
    def test_bool_prob(self):
        with self.assertRaises(ValueError):probability(True)
    def test_float_prob(self):
        with self.assertRaises(ValueError):probability(.5)
    def test_zero_denominator(self):
        with self.assertRaises(ValueError):probability('1/0')
    def test_missing_calibration_field(self):
        p,c,d=fixture();del c['id']
        with self.assertRaises(ValueError):audit(p,c,d)
    def test_missing_deployment_field(self):
        p,c,d=fixture();del d['day']
        with self.assertRaises(ValueError):audit(p,c,d)
    def test_reversed_window(self):
        p,c,d=fixture();c['from_day']=101
        with self.assertRaises(ValueError):audit(p,c,d)
    def test_bad_day(self):
        p,c,d=fixture();d['day']=-3
        with self.assertRaises(ValueError):audit(p,c,d)
    def test_bool_day(self):
        p,c,d=fixture();d['day']=True
        with self.assertRaises(ValueError):audit(p,c,d)
    def test_bad_n(self):
        p,c,d=fixture();c['n']='120'
        with self.assertRaises(ValueError):audit(p,c,d)
    def test_bad_likelihood_keys(self):
        p,c,d=fixture();c['likelihoods']={'0101':'1/2'}
        with self.assertRaises(ValueError):audit(p,c,d)
    def test_bad_rate_keys(self):
        p,c,d=fixture();d['observed_rates']={'other':'1/2'}
        with self.assertRaises(ValueError):audit(p,c,d)
    def test_bad_identifier(self):
        p,c,d=fixture();c['population']='lab A'
        with self.assertRaises(ValueError):audit(p,c,d)
    def test_bad_policy_age(self):
        with self.assertRaises(ValueError):audit(*fixture(),max_age=True)
    def test_bad_policy_n(self):
        with self.assertRaises(ValueError):audit(*fixture(),min_n=0)
    def test_bad_policy_gap(self):
        with self.assertRaises(ValueError):audit(*fixture(),max_rate_gap='2')
    def test_unspecified_fixture(self):
        with self.assertRaises(ValueError):fixture('unknown')
    def test_equal_rate_nonproof(self):
        p,c,d=fixture();d['observed_rates']['positive']='1/2';r=audit(p,c,d)
        self.assertIn('Single summary rate cannot rule out calibration drift or concept shift',r['limitations'])
    def test_metadata_not_authenticated(self):self.assertIn('not authenticated',self.run_case('current')['caveat'])
    def test_true_frozen_parent(self):self.assertTrue(demo()['frozen_parent'])

if __name__=='__main__':unittest.main()