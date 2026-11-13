import unittest
from dataclasses import FrozenInstanceError
from boundary import Operation,Declaration,FLAY,compare,demo

class BoundaryTests(unittest.TestCase):
    def test_core_compatible(self): self.assertTrue(demo()[1]['core_verified'])
    def test_left_fail(self): self.assertEqual(demo()[1]['first_failure']['left']['state'],-1)
    def test_left_reason(self): self.assertEqual(demo()[1]['first_failure']['left']['reason'],'INVALID_ORDER')
    def test_no_right_failure(self): self.assertIsNone(demo()[1]['first_failure']['right'])
    def test_right_progress(self): self.assertEqual(demo()[1]['tested_outside']['right'],[4,5,6])
    def test_core_count(self): self.assertEqual(demo()[1]['core_count'],4)
    def test_trial_count(self): self.assertEqual(demo()[1]['states_tested_outside'],4)
    def test_status(self): self.assertEqual(demo()[1]['status'],'BOUNDARY_COUNTEREXAMPLE')
    def test_scope(self): self.assertIn('finite',demo()[1]['scope'])
    def test_no_learning(self): self.assertFalse(demo()[1]['learning_applied'])
    def test_parent(self): self.assertEqual(demo()[1]['active'],'frozen_parent')
    def test_no_new_witness(self): self.assertEqual(demo()[1]['independent_witness_increment'],0)
    def test_deterministic(self): self.assertEqual(demo()[1],demo()[1])
    def test_audit(self): self.assertEqual(demo()[0].audit(),'VALID_LOCAL_CHAIN')
    def test_audit_tamper(self):
        f,_=demo();f.events[1]['kind']='FORGED';self.assertEqual(f.audit(),'TAMPERED')
    def test_anchor(self): self.assertEqual(demo()[0].audit('0'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_zero_budget(self):
        f=FLAY(Operation('add',1),Operation('add',2),Declaration(0,3,0))
        self.assertEqual(f.explore()['states_tested_outside'],0)
    def test_one_step(self):
        f=FLAY(Operation('set',0),Operation('nonnegative_add',0),Declaration(0,3,1))
        self.assertEqual(f.explore()['states_tested_outside'],1)
    def test_invalid_core(self):
        f=FLAY(Operation('set',0),Operation('nonnegative_add',0),Declaration(-1,1,2))
        self.assertEqual(f.explore()['status'],'CORE_INVALID')
    def test_commuting_expansion(self):
        f=FLAY(Operation('add',1),Operation('add',2),Declaration(0,2,4))
        self.assertEqual(f.explore()['status'],'BUDGET_OR_DOMAIN_LIMIT')
    def test_invalid_range(self):
        with self.assertRaises(ValueError):Declaration(4,3,2)
    def test_huge_range(self):
        with self.assertRaises(ValueError):Declaration(0,65,2)
    def test_negative_budget(self):
        with self.assertRaises(ValueError):Declaration(0,1,-1)
    def test_large_budget(self):
        with self.assertRaises(ValueError):Declaration(0,1,129)
    def test_float_domain(self):
        with self.assertRaises(ValueError):Declaration(0.0,1,1)
    def test_bad_operation(self):
        with self.assertRaises(ValueError):Operation('divide',1)
    def test_frozen_op(self):
        with self.assertRaises(FrozenInstanceError):Operation('add',1).argument=2
    def test_bad_parent_hash(self):
        with self.assertRaises(ValueError):FLAY(Operation('add',1),Operation('add',2),Declaration(0,2,1),'x')
    def test_noncommuting_arithmetic(self):self.assertFalse(compare(2,Operation('add',3),Operation('multiply',2))['compatible'])
    def test_same_arithmetic(self):self.assertTrue(compare(2,Operation('add',3),Operation('add',4))['compatible'])
    def test_negative_precondition(self):self.assertFalse(compare(-1,Operation('set',0),Operation('nonnegative_add',0))['compatible'])
    def test_positive_precondition(self):self.assertTrue(compare(4,Operation('set',0),Operation('nonnegative_add',0))['compatible'])
    def test_invalid_floor(self):
        with self.assertRaises(ValueError):Declaration(0,2,2,floor=1)
    def test_boundary_clamp(self):
        f=FLAY(Operation('add',1),Operation('add',2),Declaration(0,1,20,floor=0,ceiling=1))
        self.assertEqual(f.explore()['states_tested_outside'],0)
    def test_has_chronos(self):self.assertIn('2026.11.13',demo()[1]['chronos'])
    def test_digest(self):self.assertEqual(len(demo()[1]['digest']),64)

if __name__=='__main__':unittest.main(verbosity=2)
