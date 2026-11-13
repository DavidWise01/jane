import unittest
from multiforce import Region, Force, FLAY157, demonstration, digest

class MultiforceTests(unittest.TestCase):
    def setUp(self):
        self.engine,self.report,self.restricted,self.restricted_report=demonstration()
    def test_main_fails(self):self.assertEqual(self.report['status'],'MULTIFORCE_COUNTEREXAMPLES')
    def test_reflection_passes(self):self.assertTrue(self.report['forces'][0]['preserves'])
    def test_increment_fails(self):self.assertFalse(self.report['forces'][1]['preserves'])
    def test_doubling_fails(self):self.assertFalse(self.report['forces'][2]['preserves'])
    def test_increment_counterexample(self):self.assertEqual(self.report['forces'][1]['smallest_failure']['state'],20)
    def test_increment_next(self):self.assertEqual(self.report['forces'][1]['smallest_failure']['next_state'],21)
    def test_doubling_counterexample(self):self.assertEqual(self.report['forces'][2]['smallest_failure']['state'],11)
    def test_doubling_next(self):self.assertEqual(self.report['forces'][2]['smallest_failure']['next_state'],22)
    def test_reflection_endpoints(self):self.assertEqual(self.report['forces'][0]['endpoint_images'],[20,0])
    def test_increment_endpoints(self):self.assertEqual(self.report['forces'][1]['endpoint_images'],[1,21])
    def test_doubling_endpoints(self):self.assertEqual(self.report['forces'][2]['endpoint_images'],[0,40])
    def test_two_failures_retained(self):self.assertEqual([x['kind'] for x in self.engine.events].count('COUNTEREXAMPLE'),2)
    def test_restricted_proven(self):self.assertEqual(self.restricted_report['status'],'MULTIFORCE_INVARIANT_PROVEN')
    def test_restricted_inductive(self):self.assertTrue(self.restricted_report['inductive'])
    def test_original_unchanged(self):self.assertTrue(self.report['parent_unchanged'])
    def test_no_learning(self):self.assertFalse(self.report['learning_applied'])
    def test_no_real_witness(self):self.assertEqual(self.report['independent_witnesses_observed'],0)
    def test_no_jane_activation(self):self.assertEqual(self.report['jane_decision'],'UNDECIDED')
    def test_all_forces_required(self):self.assertFalse(self.report['all_transitions_preserve'])
    def test_initial_valid(self):self.assertTrue(self.report['initial_inside'])
    def test_initial_outside(self):
        x=FLAY157(Region(0,20),21,[Force('identity',1,0)]).evaluate()
        self.assertEqual(x['status'],'INITIAL_OUTSIDE_REGION')
    def test_initial_outside_not_inductive(self):
        self.assertFalse(FLAY157(Region(0,20),21,[Force('identity',1,0)]).evaluate()['inductive'])
    def test_affine_negative_slope(self):
        self.assertTrue(FLAY157(Region(-2,2),0,[Force('negate',-1,0)]).evaluate()['inductive'])
    def test_affine_constant(self):
        self.assertTrue(FLAY157(Region(0,20),0,[Force('fix',0,10)]).evaluate()['inductive'])
    def test_constant_outside(self):
        self.assertEqual(FLAY157(Region(0,20),0,[Force('fix',0,21)]).evaluate()['forces'][0]['smallest_failure']['state'],0)
    def test_lower_counterexample(self):
        self.assertEqual(FLAY157(Region(0,20),0,[Force('minus',1,-1)]).evaluate()['forces'][0]['smallest_failure']['state'],0)
    def test_nonzero_region(self):
        self.assertEqual(FLAY157(Region(10,12),10,[Force('add',1,1)]).evaluate()['forces'][0]['smallest_failure']['state'],12)
    def test_singleton(self):
        self.assertTrue(FLAY157(Region(4,4),4,[Force('fix',0,4)]).evaluate()['inductive'])
    def test_tamper(self):
        self.engine.events[-1]['data']['state']=123
        self.assertEqual(self.engine.audit(),'LEDGER_TAMPERED')
    def test_ledger(self):self.assertEqual(self.engine.audit(),'VALID_LOCAL_CHAIN')
    def test_head_mismatch(self):self.assertEqual(self.engine.audit('0'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_determinism(self):self.assertEqual(demonstration()[1],demonstration()[1])
    def test_digest(self):self.assertEqual(len(self.report['digest']),64)
    def test_bad_region_order(self):
        with self.assertRaises(ValueError):Region(2,1)
    def test_large_region(self):
        with self.assertRaises(ValueError):Region(0,257)
    def test_bad_region_type(self):
        with self.assertRaises(ValueError):Region(0.0,20)
    def test_bad_force_type(self):
        with self.assertRaises(ValueError):Force('bad',True,0)
    def test_bad_force_name(self):
        with self.assertRaises(ValueError):Force('',1,0)
    def test_duplicate_name(self):
        with self.assertRaises(ValueError):FLAY157(Region(0,1),0,[Force('x',1,0),Force('x',0,0)])
    def test_empty_forces(self):
        with self.assertRaises(ValueError):FLAY157(Region(0,1),0,[])
    def test_bad_parent_head(self):
        with self.assertRaises(ValueError):FLAY157(Region(0,1),0,[Force('x',1,0)],'not-a-digest')
    def test_append_only_after_evaluate(self):
        self.assertEqual(self.engine.events[0]['kind'],'DECLARED')
    def test_ledger_contains_report_digest(self):
        self.assertEqual(self.engine.events[1]['data']['report_digest'],self.report['digest'])
    def test_bounded_force_count(self):
        with self.assertRaises(ValueError):FLAY157(Region(0,1),0,[Force(str(i),1,0) for i in range(17)])
    def test_no_universal_claim(self):self.assertIn('declared',self.report['model_scope'])
if __name__=='__main__': unittest.main(verbosity=2)