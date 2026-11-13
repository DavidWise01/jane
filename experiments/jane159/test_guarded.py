import unittest
from guarded import Rule,FLAY159,demo

class TestJANE159(unittest.TestCase):
    def e(self, rules, **kwargs): return FLAY159(0,rules,**kwargs).run()
    def test_guarded_bounded(self): self.assertEqual(demo()['guarded']['status'],'BOUNDED_REACHABLE_SET')
    def test_guarded_complete(self): self.assertTrue(demo()['guarded']['complete'])
    def test_guarded_count(self): self.assertEqual(demo()['guarded']['states_seen'],21)
    def test_guarded_no_breach(self): self.assertIsNone(demo()['guarded']['counterexample'])
    def test_guarded_no_unbounded_certificate(self): self.assertIsNone(demo()['guarded']['unbounded_path_certificate'])
    def test_unconditional_breach(self): self.assertEqual(demo()['unconditional']['status'],'BOUND_VIOLATED')
    def test_unconditional_certificate(self): self.assertEqual(demo()['unconditional']['unbounded_path_certificate']['delta'],1)
    def test_unconditional_first_breach(self): self.assertEqual(demo()['unconditional']['counterexample']['to'],21)
    def test_unconditional_path_length(self): self.assertEqual(len(demo()['unconditional']['counterexample']['path']),21)
    def test_unconditional_incomplete(self): self.assertFalse(demo()['unconditional']['complete'])
    def test_guarded_deterministic(self): self.assertEqual(demo()['guarded'],demo()['guarded'])
    def test_same_head(self):
        f=FLAY159(0,[Rule('inc',1,'lt',2)]); f.run(); self.assertEqual(f.audit(f.entries[-1]['hash']),'LOCAL_LEDGER_VALID')
    def test_wrong_external_head(self):
        f=FLAY159(0,[Rule('inc',1,'lt',2)]); self.assertEqual(f.audit('0'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_ledger_tamper(self):
        f=FLAY159(0,[Rule('inc',1,'lt',2)]); f.entries[0]['kind']='FAKE'; self.assertEqual(f.audit(),'LOCAL_LEDGER_TAMPERED')
    def test_guard_strict(self): self.assertFalse(Rule('x',1,'lt',20).enabled(20))
    def test_guard_le(self): self.assertTrue(Rule('x',1,'le',20).enabled(20))
    def test_guard_ge(self): self.assertTrue(Rule('x',1,'ge',20).enabled(20))
    def test_guard_gt(self): self.assertFalse(Rule('x',1,'gt',20).enabled(20))
    def test_guard_eq(self): self.assertTrue(Rule('x',1,'eq',20).enabled(20))
    def test_disabled_rejects(self):
        with self.assertRaises(ValueError):Rule('x',1,'lt',20).apply(20)
    def test_noop_closed(self): self.assertEqual(self.e([Rule('zero',0)])['status'],'BOUNDED_REACHABLE_SET')
    def test_negative_drift_breach(self):self.assertEqual(self.e([Rule('decrement',-1)])['counterexample']['to'],-1)
    def test_negative_drift_no_positive_certificate(self):self.assertIsNone(self.e([Rule('decrement',-1)])['unbounded_path_certificate'])
    def test_single_jump_breach(self):self.assertEqual(self.e([Rule('jump',30)])['counterexample']['to'],30)
    def test_conditional_jump(self):self.assertEqual(self.e([Rule('jump',30,'eq',4)])['status'],'BOUNDED_REACHABLE_SET')
    def test_multiple_forces(self):self.assertEqual(self.e([Rule('reflect_stop',0),Rule('increment',1,'lt',20)])['states_seen'],21)
    def test_order_invariance(self):
        a=[Rule('a',1,'lt',3),Rule('b',0)]
        self.assertEqual(self.e(a),self.e(a[::-1]))
    def test_short_budget_unknown(self):self.assertEqual(self.e([Rule('inc',1,'lt',20)],max_states=5)['status'],'INCONCLUSIVE_BUDGET')
    def test_short_budget_not_proof(self):self.assertFalse(self.e([Rule('inc',1,'lt',20)],max_states=5)['complete'])
    def test_reject_unknown_guard(self):
        with self.assertRaises(ValueError):Rule('x',1,'python_eval',0)
    def test_reject_bad_delta(self):
        with self.assertRaises(ValueError):Rule('x',1.2)
    def test_reject_duplicate_rules(self):
        with self.assertRaises(ValueError):FLAY159(0,[Rule('x',1),Rule('x',2)])
    def test_reject_bad_budget(self):
        with self.assertRaises(ValueError):FLAY159(0,[Rule('x',1)],max_states=0)
    def test_reject_bounds(self):
        with self.assertRaises(ValueError):FLAY159(0,[Rule('x',1)],lower=2,upper=1)
    def test_reject_empty_rules(self):
        with self.assertRaises(ValueError):FLAY159(0,[])
    def test_no_automatic_learning(self):self.assertFalse(demo()['guarded']['learning_applied'])
    def test_no_votes(self):self.assertEqual(demo()['guarded']['witness_votes_added'],0)
    def test_frozen(self):self.assertEqual(demo()['guarded']['active_parent'],'FROZEN')
    def test_initial_outside_claim(self):
        r=FLAY159(25,[Rule('hold',0)],0,20).run()
        # Out-of-bound initial state is independently a failed claimed invariant.
        self.assertNotEqual(r['status'],'BOUNDED_REACHABLE_SET')

if __name__=='__main__':unittest.main(verbosity=2)