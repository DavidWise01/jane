import unittest
from copy import deepcopy
from impossibility import (Transition, Interval, verify_local_interval,
                           positive_escape, negative_escape, impossibility_certificate,
                           verify_certificate, FLAY158, Ledger, demo)

class InvariantTests(unittest.TestCase):
    def test_increment_impossible(self): self.assertEqual(demo()[1]['status'], 'PROVEN_NO_BOUNDED_INTERVAL')
    def test_demo_forces(self): self.assertEqual(len(demo()[1]['declared_forces']), 2)
    def test_demo_certificates(self): self.assertEqual(len(demo()[1]['certificates']), 1)
    def test_demo_budget(self): self.assertEqual(len(demo()[1]['candidate_checks']), 6)
    def test_increment_certificate(self): self.assertTrue(verify_certificate(demo()[1]['certificates'][0]))
    def test_decrement_certificate(self): self.assertTrue(verify_certificate(impossibility_certificate(0, Transition('down', 'shift', -2))))
    def test_zero_shift_not_proof(self): self.assertIsNone(impossibility_certificate(0, Transition('stay', 'shift', 0)))
    def test_reflection_not_proof(self): self.assertIsNone(impossibility_certificate(0, Transition('flip', 'reflect', 20)))
    def test_guarded_not_proof(self): self.assertIsNone(impossibility_certificate(0, Transition('guard', 'shift', 1, False)))
    def test_set_not_proof(self): self.assertIsNone(impossibility_certificate(0, Transition('set', 'set', 5)))
    def test_no_proof_reflection(self): self.assertEqual(FLAY158(0, [Transition('flip', 'reflect', 20)]).evaluate()['status'], 'NO_IMPOSSIBILITY_PROOF')
    def test_reflection_interval(self): self.assertEqual(verify_local_interval(0, Interval(0,20), [Transition('flip','reflect',20)])['status'], 'INDUCTIVE_INTERVAL')
    def test_set_interval(self): self.assertEqual(verify_local_interval(0, Interval(0,10), [Transition('set','set',5)])['status'], 'INDUCTIVE_INTERVAL')
    def test_zero_shift_interval(self): self.assertEqual(verify_local_interval(0, Interval(0,0), [Transition('stay','shift',0)])['status'], 'INDUCTIVE_INTERVAL')
    def test_increment_interval(self): self.assertEqual(verify_local_interval(0, Interval(0,20), [Transition('plus','shift',1)])['status'], 'NOT_INDUCTIVE')
    def test_decrement_interval(self): self.assertEqual(verify_local_interval(0, Interval(-20,0), [Transition('minus','shift',-1)])['status'], 'NOT_INDUCTIVE')
    def test_guard_not_certified(self): self.assertEqual(verify_local_interval(0, Interval(0,5), [Transition('x','shift',1,False)])['status'], 'UNMODELED_GUARD')
    def test_initial_outside(self): self.assertEqual(verify_local_interval(11, Interval(0,10), [Transition('stay','shift',0)])['status'], 'INITIAL_OUTSIDE')
    def test_exact_escape_positive(self): self.assertEqual(positive_escape(0,20,1)['steps'],21)
    def test_exact_escape_large_positive(self): self.assertEqual(positive_escape(0,20,3)['end'],21)
    def test_exact_escape_negative(self): self.assertEqual(negative_escape(0,-20,-2)['steps'],11)
    def test_exact_escape_negative_result(self): self.assertEqual(negative_escape(0,-20,-2)['end'],-22)
    def test_bad_escape_pos(self):
        with self.assertRaises(ValueError): positive_escape(0,10,0)
    def test_bad_escape_neg(self):
        with self.assertRaises(ValueError): negative_escape(0,-10,1)
    def test_tampered_certificate(self):
        p=impossibility_certificate(0, Transition('up','shift',1));p['step']=2
        self.assertFalse(verify_certificate(p))
    def test_malformed_certificate(self): self.assertFalse(verify_certificate({'a':1}))
    def test_no_generalization(self): self.assertTrue(demo()[1]['sample_failures_are_not_proof'])
    def test_parent_frozen(self): self.assertEqual(demo()[1]['parent'], 'FROZEN')
    def test_no_activation(self): self.assertFalse(demo()[1]['jane_activation'])
    def test_no_external_custody(self): self.assertFalse(demo()[1]['external_custody_verified'])
    def test_local_audit(self): self.assertEqual(demo()[0].ledger.verify(),'VALID_LOCAL_CHAIN')
    def test_external_anchor(self): self.assertEqual(demo()[0].ledger.verify('0'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_tampered_log(self):
        f,_=demo();f.ledger.events[0]['kind']='REWRITE';self.assertEqual(f.ledger.verify(),'CHAIN_BROKEN')
    def test_determinism(self): self.assertEqual(demo()[1],demo()[1])
    def test_invalid_interval(self):
        with self.assertRaises(ValueError): Interval(2,1)
    def test_invalid_transition_kind(self):
        with self.assertRaises(ValueError): Transition('bad','magic',0)
    def test_invalid_transition_bool(self):
        with self.assertRaises(ValueError): Transition('bad','shift',1,1)
    def test_invalid_duplicate_name(self):
        with self.assertRaises(ValueError): FLAY158(0,[Transition('same','shift',1),Transition('same','shift',2)])
    def test_bad_budget(self):
        with self.assertRaises(ValueError): FLAY158(0,[Transition('up','shift',1)],100)
    def test_bad_initial(self):
        with self.assertRaises(ValueError): FLAY158(True,[Transition('up','shift',1)])
    def test_guarded_stays_unknown(self): self.assertEqual(FLAY158(0,[Transition('maybe','shift',1,False)]).evaluate()['status'],'NO_IMPOSSIBILITY_PROOF')
    def test_negative_translation_any_bound(self):
        p=impossibility_certificate(9,Transition('negative','shift',-5));self.assertTrue(verify_certificate(p))
    def test_multiple_sufficient_forces(self): self.assertEqual(len(FLAY158(0,[Transition('up','shift',1),Transition('down','shift',-1)]).evaluate()['certificates']),2)
    def test_all_failed_is_not_proof(self):
        r=FLAY158(0,[Transition('flip','reflect',20)],max_candidates=2).evaluate();self.assertEqual(r['status'],'NO_IMPOSSIBILITY_PROOF')
    def test_ledger_append(self): self.assertEqual(len(demo()[0].ledger.events),8)

if __name__=='__main__': unittest.main(verbosity=2)