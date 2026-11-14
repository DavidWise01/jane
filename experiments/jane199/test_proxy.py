import unittest
from dataclasses import replace
from fractions import Fraction
from proxy import Record,Model,Calibration,FLAY199,fixture,digest

class TestJANE199(unittest.TestCase):
    def setUp(self):
        self.rows,self.models,self.cal=fixture()
        self.flay=FLAY199(self.rows)
    def test_01_result(self):
        self.assertEqual(self.flay.evaluate(self.models,self.cal)['verdict'],'PROXY_CAUSAL_NONIDENTIFIABILITY')
    def test_02_population(self): self.assertEqual(len(self.rows),16)
    def test_03_selected(self): self.assertEqual(sum(r.selected for r in self.rows),8)
    def test_04_missing(self): self.assertEqual(sum(not r.selected for r in self.rows),8)
    def test_05_proxy_all(self): self.assertTrue(all(r.proxy in (0,1) for r in self.rows))
    def test_06_five_successes(self): self.assertEqual(sum(r.outcome for r in self.rows if r.selected),5)
    def test_07_lower(self): self.assertEqual(self.flay.evaluate(self.models)['assumption_free_bounds']['lower']['numerator'],5)
    def test_08_upper(self): self.assertEqual(self.flay.evaluate(self.models)['assumption_free_bounds']['upper']['numerator'],13)
    def test_09_frozen(self): self.assertEqual(self.flay.frozen,digest([r.__dict__ for r in self.rows]))
    def test_10_order_independent(self): self.assertEqual(FLAY199(reversed(self.rows)).frozen,self.flay.frozen)
    def test_11_parent(self): self.assertEqual(self.flay.evaluate(self.models)['parent'],'FROZEN')
    def test_12_no_learning(self): self.assertFalse(self.flay.evaluate(self.models)['learning_applied'])
    def test_13_no_identification(self): self.assertFalse(self.flay.evaluate(self.models)['causal_identified'])
    def test_14_model_a_rate(self): self.assertEqual(self.flay.evaluate(self.models)['candidates'][0]['candidate_rate']['numerator'],5)
    def test_15_model_b_rate(self): self.assertEqual(self.flay.evaluate(self.models)['candidates'][1]['candidate_rate']['numerator'],13)
    def test_16_proxy_observed_agreement(self): self.assertEqual(self.flay.evaluate(self.models)['candidates'][0]['observed_proxy_accuracy']['percent'],100)
    def test_17_proxy_observed_agreement_b(self): self.assertEqual(self.flay.evaluate(self.models)['candidates'][1]['observed_proxy_accuracy']['percent'],100)
    def test_18_proxy_missing_disagree(self): self.assertEqual(self.flay.evaluate(self.models)['candidates'][1]['unobserved_proxy_accuracy_HYPOTHETICAL']['percent'],0)
    def test_19_proxy_missing_agree(self): self.assertEqual(self.flay.evaluate(self.models)['candidates'][0]['unobserved_proxy_accuracy_HYPOTHETICAL']['percent'],100)
    def test_20_calibration_coverage(self): self.assertEqual(self.flay.evaluate(self.models,self.cal)['calibration']['coverage'],'SELECTED_ONLY')
    def test_21_calibration_not_independent(self): self.assertFalse(self.flay.evaluate(self.models,self.cal)['calibration']['independent_custody_verified'])
    def test_22_no_calibration(self): self.assertIsNone(self.flay.evaluate(self.models)['calibration'])
    def test_23_single_model(self): self.assertEqual(self.flay.evaluate(self.models[:1])['verdict'],'SINGLE_COMPATIBLE_MODEL_NOT_IDENTIFIED')
    def test_24_no_compatible(self): self.assertEqual(self.flay.evaluate((Model('bad',(0,)*16,'root'),))['verdict'],'NO_COMPATIBLE_PROXY_MODEL')
    def test_25_duplicate_names(self):
        with self.assertRaises(ValueError): self.flay.evaluate((self.models[0],self.models[0]))
    def test_26_wrong_length(self):
        with self.assertRaises(ValueError): self.flay.evaluate((Model('short',(0,),'root'),))
    def test_27_non_selected_calibration(self):
        with self.assertRaises(ValueError): self.flay.evaluate(self.models,Calibration((6,),'root','up'))
    def test_28_out_of_range_calibration(self):
        with self.assertRaises(ValueError): self.flay.evaluate(self.models,Calibration((80,),'root','up'))
    def test_29_chain(self):
        self.flay.evaluate(self.models);self.assertEqual(self.flay.chain_status(),'VALID_LOCAL_CHAIN')
    def test_30_chain_tamper(self):
        self.flay.evaluate(self.models);self.flay.history[1]['body']['verdict']='FORGED';self.assertEqual(self.flay.chain_status(),'TAMPERED')
    def test_31_repeated_id(self):
        with self.assertRaises(ValueError): FLAY199((self.rows[0],self.rows[0]))
    def test_32_invalid_proxy(self):
        with self.assertRaises(ValueError): replace(self.rows[0],proxy=2)
    def test_33_unknown_selected(self):
        with self.assertRaises(ValueError): replace(self.rows[0],outcome=None)
    def test_34_known_missing(self):
        with self.assertRaises(ValueError): replace(self.rows[6],outcome=1)
    def test_35_invalid_boolean(self):
        with self.assertRaises(ValueError): replace(self.rows[0],selected=1)
    def test_36_invalid_id(self):
        with self.assertRaises(ValueError): replace(self.rows[0],round_id=-1)
    def test_37_invalid_model(self):
        with self.assertRaises(ValueError): Model('x',(2,),'root')
    def test_38_duplicate_calibration(self):
        with self.assertRaises(ValueError): Calibration((0,0),'root','up')
    def test_39_empty(self):
        with self.assertRaises(ValueError): FLAY199([])
    def test_40_calibration_must_be_type(self):
        with self.assertRaises(ValueError): self.flay.evaluate(self.models,{'indices':[0]})
    def test_41_immutable_calibration(self):
        self.assertEqual(self.flay.evaluate(self.models,self.cal)['calibration']['rows'],8)

if __name__=='__main__':unittest.main()