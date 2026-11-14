import unittest
from dataclasses import replace
from validation import Case, Plan, FLAY200, fixture, digest, ratio

class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.biased, self.balanced = fixture()
        self.flay = FLAY200(self.cases)

    def test_biased_perfect(self):
        r = self.flay.audit(self.biased)
        self.assertEqual(r['selected_accuracy']['percent'], 100)
        self.assertEqual(r['verdict'], 'NO_STRATUM_SUPPORT')
        self.assertFalse(r['population_generalization_proven'])

    def test_balanced_accuracy(self):
        r = self.flay.audit(self.balanced)
        self.assertEqual(r['selected_accuracy']['percent'], 50)
        self.assertEqual(r['conditional_stratified_estimate']['percent'], 50)
        self.assertEqual(r['verdict'], 'COVERAGE_BALANCED_NOT_PROVEN_RANDOM')

    def test_true_population_only_fixture(self):
        for p in (self.biased,self.balanced):
            self.assertEqual(self.flay.audit(p)['population_truth_in_synthetic_fixture']['percent'],50)

    def test_selected_bounds(self):
        self.assertEqual(self.flay.audit(self.biased)['factual_bounds_from_selected_labels']['lower']['percent'],50)
        self.assertEqual(self.flay.audit(self.biased)['factual_bounds_from_selected_labels']['upper']['percent'],100)

    def test_no_support(self):
        r = self.flay.audit(self.biased)
        self.assertIsNone(r['conditional_stratified_estimate'])
        self.assertIn('POSITIVITY_FAILURE',r['flags'])

    def test_exclusions_retained(self):
        self.assertEqual(self.flay.audit(self.biased)['excluded_ids'],[f'{i:03}' for i in range(8,16)])

    def test_population_frozen(self):
        d=self.flay.frozen_digest
        self.flay.audit(self.biased)
        self.flay.audit(self.balanced)
        self.assertEqual(d,self.flay.frozen_digest)

    def test_audit_chain(self):
        self.flay.audit(self.biased)
        self.assertTrue(self.flay.verify_chain())

    def test_chain_tampering(self):
        self.flay.history[0]['body']['population_digest']='bad'
        self.assertFalse(self.flay.verify_chain())

    def test_determinism_order(self):
        f=FLAY200(tuple(reversed(self.cases)))
        self.assertEqual(f.frozen_digest,self.flay.frozen_digest)
        self.assertEqual(f.audit(self.biased)['digest'],self.flay.audit(self.biased)['digest'])

    def test_duplicate_case_rejected(self):
        with self.assertRaises(ValueError): FLAY200(self.cases+(self.cases[0],))

    def test_empty_case_rejected(self):
        with self.assertRaises(ValueError): FLAY200([])

    def test_bad_case_type(self):
        with self.assertRaises(ValueError): FLAY200([{}])

    def test_bad_case_prediction(self):
        with self.assertRaises(ValueError): Case('a','s',2,1,'root')

    def test_bad_case_label(self):
        with self.assertRaises(ValueError): Case('a','s',1,3,'root')

    def test_bad_case_identity(self):
        with self.assertRaises(ValueError): Case('','s',1,1,'root')

    def test_duplicate_plan_inclusion(self):
        with self.assertRaises(ValueError): replace(self.biased,included=('000','000'))

    def test_duplicate_frame(self):
        with self.assertRaises(ValueError): replace(self.biased,declared_population=('000','000'))

    def test_bad_probability(self):
        with self.assertRaises(ValueError): replace(self.biased,probability_by_stratum=(('EASY',2,1),('HARD',0,1)))

    def test_zero_denominator(self):
        with self.assertRaises(ValueError): replace(self.biased,probability_by_stratum=(('EASY',1,0),('HARD',0,1)))

    def test_duplicate_prob_stratum(self):
        with self.assertRaises(ValueError): replace(self.biased,probability_by_stratum=(('EASY',1,2),('EASY',1,2)))

    def test_missing_prob_stratum(self):
        with self.assertRaises(ValueError): self.flay.audit(replace(self.biased,probability_by_stratum=(('EASY',1,1),)))

    def test_wrong_frame(self):
        with self.assertRaises(ValueError): self.flay.audit(replace(self.biased,declared_population=self.biased.declared_population[:-1]))

    def test_extra_selected(self):
        with self.assertRaises(ValueError): self.flay.audit(replace(self.biased,included=self.biased.included+('XYZ',)))

    def test_plan_type(self):
        with self.assertRaises(TypeError): self.flay.audit('wrong')

    def test_unlabeled_selected(self):
        cases=list(self.cases)
        cases[0]=replace(cases[0],label=None)
        a=FLAY200(cases).audit(self.biased)
        self.assertIn('MISSING_VALIDATION_LABELS',a['flags'])
        self.assertIsNone(a['population_truth_in_synthetic_fixture'])

    def test_one_source_root(self):
        cases=tuple(replace(c,ancestry='SAME') for c in self.cases)
        self.assertIn('INSUFFICIENT_DECLARED_SOURCE_ANCESTRY',FLAY200(cases).audit(self.balanced)['flags'])

    def test_empty_included(self):
        r=self.flay.audit(replace(self.balanced,included=()))
        self.assertIsNone(r['selected_accuracy'])
        self.assertEqual(r['verdict'],'NO_STRATUM_SUPPORT')

    def test_no_labels(self):
        cases=tuple(replace(c,label=None) for c in self.cases)
        r=FLAY200(cases).audit(self.balanced)
        self.assertIsNone(r['conditional_stratified_estimate'])
        self.assertEqual(r['factual_bounds_from_selected_labels']['upper']['percent'],100)

    def test_all_included(self):
        p=replace(self.balanced,included=tuple(c.ident for c in self.cases))
        r=self.flay.audit(p)
        self.assertEqual(r['selected_accuracy']['percent'],50)
        self.assertEqual(r['factual_bounds_from_selected_labels']['lower']['percent'],50)
        self.assertEqual(r['factual_bounds_from_selected_labels']['upper']['percent'],50)
        self.assertFalse(r['random_selection_verified'])

    def test_labels_binary_bool_rejected(self):
        with self.assertRaises(ValueError): Case('a','s',1,True,'r')

    def test_predictions_binary_bool_rejected(self):
        with self.assertRaises(ValueError): Case('a','s',False,1,'r')

    def test_population_flags(self):
        r=self.flay.audit(self.biased)
        self.assertEqual(r['parent'],'FROZEN')
        self.assertFalse(r['learning_applied'])

    def test_chain_sequence(self):
        self.flay.audit(self.biased)
        self.flay.history[1]['seq']=7
        self.assertFalse(self.flay.verify_chain())

    def test_ratio(self):
        self.assertEqual(ratio(1,3)['d'],3)
        self.assertIsNone(ratio(0,0))

    def test_digests(self):
        self.assertEqual(digest({'a':1,'b':2}),digest({'b':2,'a':1}))

    def test_another_stratum(self):
        cases=(Case('a','ONE',1,1,'r1'),Case('b','TWO',0,0,'r2'))
        p=Plan('p',('a','b'),('a','b'),'c','w','u',(('ONE',1,1),('TWO',1,1)))
        self.assertEqual(FLAY200(cases).audit(p)['selected_accuracy']['percent'],100)

    def test_no_invented_success(self):
        cases=list(self.cases)
        cases[12]=replace(cases[12],label=None)
        r=FLAY200(cases).audit(self.biased)
        self.assertEqual(r['observed_correct'],8)
        self.assertEqual(r['factual_bounds_from_selected_labels']['lower']['percent'],50)

    def test_partial_same_strata(self):
        p=replace(self.balanced,included=('000','001','008','009'))
        r=self.flay.audit(p)
        self.assertEqual(r['conditional_stratified_estimate']['percent'],50)

    def test_probabilities_not_empirical_proof(self):
        p=replace(self.balanced,probability_by_stratum=(('EASY',1,2),('HARD',1,2)))
        self.assertFalse(self.flay.audit(p)['random_selection_verified'])

if __name__=='__main__': unittest.main()