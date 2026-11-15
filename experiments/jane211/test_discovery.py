import unittest
from dataclasses import replace
from discovery import Plan, Subgroup, InvalidPlan, exact_pvalue, audit, fixture, digest, demo

class DiscoveryTests(unittest.TestCase):
    def setUp(self): self.plan,self.samples=fixture()
    def test_binomial_extreme(self): self.assertEqual(exact_pvalue(16,16), 2/65536)
    def test_binomial_mid(self): self.assertEqual(exact_pvalue(8,16),1.)
    def test_binomial_symmetry(self): self.assertEqual(exact_pvalue(3,16),exact_pvalue(13,16))
    def test_binomial_minimum(self): self.assertEqual(exact_pvalue(0,1),1.)
    def test_binomial_n1(self): self.assertEqual(exact_pvalue(1,1),1.)
    def test_reject_zero_trials(self):
        with self.assertRaises(InvalidPlan): exact_pvalue(0,0)
    def test_reject_negative_success(self):
        with self.assertRaises(InvalidPlan): exact_pvalue(-1,10)
    def test_reject_overfull(self):
        with self.assertRaises(InvalidPlan): exact_pvalue(11,10)
    def test_reject_bool(self):
        with self.assertRaises(InvalidPlan): exact_pvalue(True,8)
    def test_reject_float(self):
        with self.assertRaises(InvalidPlan): exact_pvalue(3.0,8)
    def test_family_size(self): self.assertEqual(audit(self.plan,self.samples,'G08')['family_size'],20)
    def test_extreme_selected(self): self.assertLess(audit(self.plan,self.samples,'G08')['selected_raw_p'],.001)
    def test_holm_adjusts(self):
        r=audit(self.plan,self.samples,'G08');self.assertGreater(r['selected_holm_p'],r['selected_raw_p'])
    def test_discovery_not_validation(self): self.assertEqual(audit(self.plan,self.samples,'G08')['verdict'],'EXPLORATORY_NOT_VALIDATED')
    def test_frozen_parent(self): self.assertTrue(audit(self.plan,self.samples,'G08')['frozen_parent'])
    def test_order_independent(self): self.assertEqual(audit(self.plan,self.samples,'G08'),audit(self.plan,list(reversed(self.samples)),'G08'))
    def test_evidence_digest(self):
        r=audit(self.plan,self.samples,'G08');h=r.pop('evidence_digest');self.assertEqual(h,digest(r))
    def test_missing_group(self):
        with self.assertRaises(InvalidPlan): audit(self.plan,self.samples[:-1],'G08')
    def test_duplicate_group(self):
        with self.assertRaises(InvalidPlan): audit(self.plan,self.samples[:-1]+[self.samples[0]],'G08')
    def test_outside_group(self):
        with self.assertRaises(InvalidPlan): audit(self.plan,self.samples,'G50')
    def test_unfrozen(self):
        with self.assertRaises(InvalidPlan): audit(replace(self.plan,frozen=False),self.samples,'G08')
    def test_duplicate_family(self):
        with self.assertRaises(InvalidPlan): audit(replace(self.plan,family=('G01',)*20),self.samples,'G08')
    def test_empty_family(self):
        with self.assertRaises(InvalidPlan): audit(replace(self.plan,family=()),[],'G08')
    def test_wrong_null(self):
        with self.assertRaises(InvalidPlan): audit(replace(self.plan,null_probability=.6),self.samples,'G08')
    def test_wrong_alpha(self):
        with self.assertRaises(InvalidPlan): audit(replace(self.plan,alpha=1.),self.samples,'G08')
    def test_missing_population(self):
        with self.assertRaises(InvalidPlan): audit(replace(self.plan,population=''),self.samples,'G08')
    def test_missing_ancestry(self):
        with self.assertRaises(InvalidPlan): audit(self.plan,[replace(self.samples[0],ancestry='')]+self.samples[1:],'G08')
    def test_validation_fail(self): self.assertEqual(demo()['validation_failed']['verdict'],'INDEPENDENT_VALIDATION_NOT_CONFIRMED')
    def test_validation_pass_fixture(self): self.assertEqual(demo()['validation_passed_fixture']['verdict'],'INDEPENDENT_VALIDATION_CONDITIONAL')
    def test_validation_leak(self): self.assertEqual(demo()['validation_leaked']['verdict'],'VALIDATION_CONTAMINATED')
    def test_selected_adjusted(self): self.assertTrue(audit(self.plan,self.samples,'G08')['selection_adjusted_discovery'])
    def test_nonselected_no_discovery(self): self.assertFalse(audit(self.plan,self.samples,'G01')['selection_adjusted_discovery'])
    def test_validation_mismatch_group(self):
        with self.assertRaises(InvalidPlan): audit(self.plan,self.samples,'G08',validation=self.validation(group='G01'))
    def test_validation_mismatch_set(self):
        with self.assertRaises(InvalidPlan): audit(self.plan,self.samples,'G08',validation=self.validation(dataset_id='different'))
    def test_validation_schema_missing(self):
        with self.assertRaises(InvalidPlan): audit(self.plan,self.samples,'G08',validation={'group':'G08'})
    def test_validation_invalid_counts(self):
        with self.assertRaises(InvalidPlan): audit(self.plan,self.samples,'G08',validation=self.validation(successes=17))
    def test_selection_influence(self): self.assertEqual(audit(self.plan,self.samples,'G08',validation=self.validation(selection_influenced=True))['verdict'],'VALIDATION_CONTAMINATED')
    def test_same_validation_prior_exposure(self): self.assertEqual(audit(self.plan,self.samples,'G08',validation=self.validation(previously_exposed=True))['verdict'],'VALIDATION_CONTAMINATED')
    def test_repeated_demo(self): self.assertEqual(demo(),demo())
    def test_plan_changes_digest(self): self.assertNotEqual(audit(self.plan,self.samples,'G08')['plan_digest'],audit(replace(self.plan,alpha=.01),self.samples,'G08')['plan_digest'])
    def test_strong_selected_not_validated(self): self.assertIsNone(audit(self.plan,self.samples,'G08')['validation'])
    def test_all_rows_present(self): self.assertEqual(set(x['group'] for x in audit(self.plan,self.samples,'G08')['rows']),set(self.plan.family))
    def test_holm_monotone(self):
        r=audit(self.plan,self.samples,'G08');ordered=sorted(r['rows'],key=lambda x:(x['raw_p'],x['group']));self.assertEqual([x['holm_p'] for x in ordered],sorted(x['holm_p'] for x in ordered))
    def validation(self,**kwargs):
        obj={'group':'G08','successes':16,'trials':16,'dataset_id':self.plan.validation_id,'previously_exposed':False,'selection_influenced':False};obj.update(kwargs);return obj

if __name__=='__main__': unittest.main()