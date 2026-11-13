import unittest
from dataclasses import replace
from conditional import Operation,Domain,FLAY,replay,demo,digest
class ConditionalTests(unittest.TestCase):
    def test_demo_counterexample(self):self.assertEqual(demo()[1]["status"],"COUNTEREXAMPLE_FOUND")
    def test_smallest_state(self):self.assertEqual(demo()[1]["smallest_counterexample"]["state"],-1)
    def test_count(self):self.assertEqual(demo()[1]["states_checked"],7)
    def test_counterexample_count(self):self.assertEqual(demo()[1]["counterexample_count"],3)
    def test_at_zero_commutes(self):
        a=Operation("set",0);b=Operation("conditional_add",0)
        self.assertEqual(replay(0,a,b)["final"],replay(0,b,a)["final"])
    def test_adds_commute(self):self.assertEqual(FLAY(Operation("add",2),Operation("add",7),Domain(-5,5)).evaluate()["status"],"COMMUTES_ON_DECLARED_DOMAIN")
    def test_multiply_commutes(self):self.assertEqual(FLAY(Operation("multiply",2),Operation("multiply",3),Domain(-3,3)).evaluate()["status"],"COMMUTES_ON_DECLARED_DOMAIN")
    def test_add_multiply_not_commute(self):self.assertEqual(FLAY(Operation("add",3),Operation("multiply",2),Domain(-2,2)).evaluate()["status"],"COUNTEREXAMPLE_FOUND")
    def test_singleton_can_commute(self):self.assertEqual(FLAY(Operation("set",0),Operation("conditional_add",0),Domain(0,0)).evaluate()["status"],"COMMUTES_ON_DECLARED_DOMAIN")
    def test_condition_precondition(self):self.assertEqual(FLAY(Operation("conditional_add",1),Operation("add",-3),Domain(-1,1)).evaluate()["status"],"COUNTEREXAMPLE_FOUND")
    def test_all_invalid_domain(self):self.assertEqual(FLAY(Operation("conditional_add",1),Operation("add",2),Domain(-5,-4)).evaluate()["status"],"DOMAIN_HAS_INVALID_STATES")
    def test_no_inference_outside_domain(self):self.assertIn("finite",demo()[1]["scope"])
    def test_immutable_parent(self):self.assertEqual(demo()[1]["active"],"frozen_parent")
    def test_no_learning(self):self.assertFalse(demo()[1]["learning_applied"])
    def test_no_new_witness(self):self.assertEqual(demo()[1]["independent_witness_increment"],0)
    def test_determinism(self):self.assertEqual(demo()[1],demo()[1])
    def test_ledger(self):self.assertEqual(demo()[0].audit(),"VALID_LOCAL_CHAIN")
    def test_external_head(self):self.assertEqual(demo()[0].audit("a"*64),"EXTERNAL_HEAD_MISMATCH")
    def test_tamper(self):
        f,_=demo();f.events[0]["kind"]="FORGED";self.assertEqual(f.audit(),"TAMPERED")
    def test_domain_size(self):
        with self.assertRaises(ValueError):Domain(0,257)
    def test_inverted_domain(self):
        with self.assertRaises(ValueError):Domain(5,4)
    def test_non_integer(self):
        with self.assertRaises(ValueError):Domain(0.0,3)
    def test_bad_operation(self):
        with self.assertRaises(ValueError):Operation("divide",2)
    def test_bad_arg(self):
        with self.assertRaises(ValueError):Operation("add",101)
    def test_bad_parent(self):
        with self.assertRaises(ValueError):FLAY(Operation("add",1),Operation("add",2),Domain(0,1),"oops")
    def test_set_vs_multiply(self):self.assertEqual(replay(2,Operation("set",0),Operation("multiply",0))["final"],0)
    def test_trace(self):self.assertEqual(replay(2,Operation("add",3),Operation("multiply",2))["trace"],[2,5,10])
    def test_empty_failure(self):self.assertIsNone(FLAY(Operation("add",1),Operation("add",2),Domain(0,2)).evaluate()["smallest_counterexample"])
    def test_sha(self):self.assertEqual(len(demo()[1]["digest"]),64)
    def test_smallest_negative_tiebreak(self):self.assertEqual(demo()[1]["smallest_counterexample"]["state"],-1)
if __name__=="__main__":unittest.main(verbosity=2)
