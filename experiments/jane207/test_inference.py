import copy
from fractions import Fraction
import unittest
from inference import audit, fixture, rational, digest


class JANE207(unittest.TestCase):
    def runmode(self, mode):
        return audit(*fixture(mode))

    def test_noisy_posterior(self):
        x = self.runmode('noisy')
        self.assertEqual(x['verdict'], 'HIGH_CONFIDENCE_UNVERIFIED')
        self.assertEqual(x['posterior'], {'0101': '2/11', '1010': '9/11'})

    def test_additional(self):
        x = self.runmode('additional')
        self.assertEqual(x['posterior'], {'0101': '2/29', '1010': '27/29'})
        self.assertEqual(x['distinct_declared_roots'], 2)

    def test_shared_ancestry(self):
        self.assertEqual(self.runmode('shared-root')['verdict'], 'SHARED_ANCESTRY_WITHHELD')

    def test_calibration(self):
        self.assertEqual(self.runmode('poor-calibration')['verdict'], 'INSUFFICIENT_CALIBRATION')

    def test_no_update(self):
        self.assertEqual(self.runmode('non-discriminating')['verdict'], 'NO_UPDATE_FROM_DECLARED_EVIDENCE')

    def test_point_mass_not_proof(self):
        self.assertEqual(self.runmode('point-mass')['verdict'], 'MODEL_CONDITIONAL_POINT_MASS')

    def test_conflict(self):
        self.assertEqual(self.runmode('conflict')['verdict'], 'ZERO_LIKELIHOOD_CONFLICT')

    def test_empty(self):
        x = audit(*fixture('noisy')[:1], []) if False else audit({'0101':'1/2', '1010':'1/2'}, [])
        self.assertEqual(x['verdict'], 'NO_UPDATE_FROM_DECLARED_EVIDENCE')

    def test_asymmetric_prior(self):
        x = audit({'0101':'3/4', '1010':'1/4'}, fixture()[1])
        self.assertEqual(x['posterior'], {'0101':'2/5','1010':'3/5'})

    def test_zero_prior_not_resurrected(self):
        x = audit({'0101':'0','1010':'1'}, fixture()[1])
        self.assertEqual(x['verdict'], 'MODEL_CONDITIONAL_POINT_MASS')

    def test_evidence_order_invariance(self):
        p,e = fixture('additional')
        self.assertEqual(audit(p,e)['posterior'], audit(p,list(reversed(e)))['posterior'])

    def test_digest_determinism(self):
        p,e=fixture()
        self.assertEqual(audit(p,e)['evidence_digest'], audit(copy.deepcopy(p),copy.deepcopy(e))['evidence_digest'])

    def test_digest_changed_on_likelihood_change(self):
        p,e=fixture()
        h=audit(p,e)['evidence_digest']
        e[0]['likelihood']['1010']='4/5'
        self.assertNotEqual(h,audit(p,e)['evidence_digest'])

    def test_duplicate_id(self):
        p,e=fixture('additional')
        e[1]['id']=e[0]['id']
        with self.assertRaises(ValueError): audit(p,e)

    def test_invalid_prior_missing(self):
        with self.assertRaises(ValueError): audit({'0101':'1'},[])

    def test_invalid_prior_extra(self):
        with self.assertRaises(ValueError): audit({'0101':'1/2','1010':'1/2','1111':'0'},[])

    def test_prior_sum(self):
        with self.assertRaises(ValueError): audit({'0101':'1/2','1010':'1/3'},[])

    def test_negative_probability(self):
        with self.assertRaises(ValueError): rational('-1/4')

    def test_probability_above_one(self):
        with self.assertRaises(ValueError): rational('5/4')

    def test_invalid_fraction(self):
        with self.assertRaises(ValueError): rational('twelve')

    def test_boolean_rejected(self):
        with self.assertRaises(ValueError): rational(True)

    def test_float_rejected(self):
        with self.assertRaises(ValueError): rational(0.2)

    def test_malformed_event(self):
        with self.assertRaises(ValueError): audit({'0101':'1/2','1010':'1/2'}, ['str'])

    def test_missing_evidence_fields(self):
        p,e=fixture(); del e[0]['root']
        with self.assertRaises(ValueError): audit(p,e)

    def test_invalid_id(self):
        p,e=fixture();e[0]['id']='bad id'
        with self.assertRaises(ValueError): audit(p,e)

    def test_invalid_root(self):
        p,e=fixture();e[0]['root']=''
        with self.assertRaises(ValueError): audit(p,e)

    def test_invalid_proxy(self):
        p,e=fixture();e[0]['proxy']='<script>'
        with self.assertRaises(ValueError): audit(p,e)

    def test_bad_calibration(self):
        p,e=fixture();e[0]['calibration_n']=-1
        with self.assertRaises(ValueError): audit(p,e)

    def test_boolean_calibration(self):
        p,e=fixture();e[0]['calibration_n']=True
        with self.assertRaises(ValueError): audit(p,e)

    def test_boolean_minimum(self):
        with self.assertRaises(ValueError): audit(*fixture(),min_calibration_n=True)

    def test_minimum_zero(self):
        with self.assertRaises(ValueError): audit(*fixture(),min_calibration_n=0)

    def test_custom_minimum(self):
        self.assertEqual(audit(*fixture('poor-calibration'),min_calibration_n=2)['verdict'], 'HIGH_CONFIDENCE_UNVERIFIED')

    def test_custom_threshold(self):
        self.assertEqual(audit(*fixture(),threshold='9/10')['verdict'], 'PROBABILISTIC_INFERENCE_ONLY')

    def test_nonlist_evidence(self):
        with self.assertRaises(ValueError): audit({'0101':'1/2','1010':'1/2'}, {})

    def test_too_many(self):
        with self.assertRaises(ValueError): audit({'0101':'1/2','1010':'1/2'}, [fixture()[1][0]] * 33)

    def test_likelihood_missing_candidate(self):
        p,e=fixture();del e[0]['likelihood']['0101']
        with self.assertRaises(ValueError): audit(p,e)

    def test_likelihood_above_one(self):
        p,e=fixture();e[0]['likelihood']['0101']='2'
        with self.assertRaises(ValueError): audit(p,e)

    def test_not_identity_proof(self):
        x=self.runmode('point-mass')
        self.assertTrue(any('not proof' in t for t in x['limitations']))

    def test_frozen_input(self):
        p,e=fixture();original=copy.deepcopy((p,e))
        audit(p,e)
        self.assertEqual((p,e),original)

    def test_root_case_sensitive(self):
        p,e=fixture('additional');e[1]['root']='SENSOR-FAM-A'
        self.assertEqual(audit(p,e)['distinct_declared_roots'],2)

    def test_exact_fraction(self):
        self.assertEqual(rational('1/3'),Fraction(1,3))


if __name__ == '__main__':
    unittest.main()