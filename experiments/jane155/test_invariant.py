import unittest
from dataclasses import FrozenInstanceError
from invariant import Rule,Invariant155,demo
class Tests(unittest.TestCase):
    def test_safe(self):self.assertEqual(demo()['safe']['status'],'INDUCTIVE_INVARIANT_CERTIFIED')
    def test_unsafe(self):self.assertEqual(demo()['unsafe']['status'],'INDUCTIVE_STEP_FAILED')
    def test_hidden_failure(self):self.assertEqual(demo()['latent']['status'],'INDUCTIVE_STEP_FAILED')
    def test_hidden_finite_sample_passes(self):self.assertEqual(demo()['latent']['finite_sample']['failures'],[])
    def test_hidden_global_counterexample(self):self.assertEqual(demo()['latent']['first_transition_counterexample']['input'],21)
    def test_hidden_output(self):self.assertEqual(demo()['latent']['first_transition_counterexample']['output'],-1)
    def test_decrement_minimum(self):self.assertEqual(Rule('d',1,-1).minimum_failure(),0)
    def test_negative_slope(self):self.assertEqual(Rule('d',-2,8).minimum_failure(),5)
    def test_zero_slope_positive(self):self.assertIsNone(Rule('d',0,2).minimum_failure())
    def test_zero_slope_negative(self):self.assertEqual(Rule('d',0,-1).minimum_failure(),0)
    def test_positive_coefficient(self):self.assertIsNone(Rule('d',10,0).minimum_failure())
    def test_negative_initial(self):self.assertEqual(Invariant155(-1,[Rule('a',1,1)]).evaluate()['status'],'INITIAL_OUTSIDE_REGION')
    def test_finite_first_state(self):self.assertEqual(Invariant155(0,[Rule('d',1,-1)]).finite_check(0)['failures'][0]['state'],0)
    def test_finite_bound(self):self.assertEqual(Invariant155(0,[Rule('a',1,1)]).finite_check(3)['transitions_tested'],4)
    def test_more_rules(self):self.assertEqual(Invariant155(0,[Rule('a',1,1),Rule('b',2,1)]).finite_check(3)['transitions_tested'],8)
    def test_no_overclaim(self):self.assertIn('finite search only',demo()['latent']['finite_sample']['meaning'])
    def test_scope(self):self.assertEqual(demo()['safe']['proof_scope'],'integer affine transitions only')
    def test_ancestry(self):self.assertEqual(demo()['safe']['source_root'],'owned:canonical')
    def test_no_witness_creation(self):self.assertEqual(demo()['safe']['independent_witness_increment'],0)
    def test_no_learning(self):self.assertFalse(demo()['safe']['learning_applied'])
    def test_parent_active(self):self.assertEqual(demo()['safe']['active'],'frozen_parent')
    def test_deterministic(self):self.assertEqual(demo(),demo())
    def test_audit(self):self.assertEqual(demo()['audits'],['VALID_LOCAL_CHAIN']*3)
    def test_tampering(self):
        f=Invariant155(0,[Rule('a',1,1)]);f.evaluate();f.events[0]['kind']='FORGED';self.assertEqual(f.audit(),'TAMPERED')
    def test_external_head(self):
        f=Invariant155(0,[Rule('a',1,1)]);f.evaluate();self.assertEqual(f.audit('f'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_duplicates(self):
        with self.assertRaises(ValueError):Invariant155(0,[Rule('a',1,0),Rule('a',2,0)])
    def test_no_rules(self):
        with self.assertRaises(ValueError):Invariant155(0,[])
    def test_budget(self):
        with self.assertRaises(ValueError):Invariant155(0,[Rule(str(i),1,0) for i in range(33)])
    def test_noninteger_rule(self):
        with self.assertRaises(ValueError):Rule('a',1.5,0)
    def test_boolean_rule(self):
        with self.assertRaises(ValueError):Rule('a',True,0)
    def test_bad_name(self):
        with self.assertRaises(ValueError):Rule('',1,0)
    def test_finite_budget(self):
        with self.assertRaises(ValueError):Invariant155(0,[Rule('a',1,0)]).finite_check(10001)
    def test_frozen_rule(self):
        with self.assertRaises(FrozenInstanceError):Rule('a',1,0).a=3
    def test_witness_root(self):
        with self.assertRaises(ValueError):Invariant155(0,[Rule('a',1,0)],witness_root='')
    def test_certified_rule_invariant(self):self.assertTrue(all(c['valid_for_all_nonnegative'] for c in demo()['safe']['certificates']))
    def test_unsafe_rule_invariant(self):self.assertFalse(demo()['unsafe']['certificates'][0]['valid_for_all_nonnegative'])
if __name__=='__main__':unittest.main(verbosity=2)
