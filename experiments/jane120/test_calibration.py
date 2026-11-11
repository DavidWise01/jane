import unittest
from fractions import Fraction as F
from calibration import Trial,evaluate,route
class TestJane120(unittest.TestCase):
 def setUp(self):
  self.rows=[Trial("lineage",F(3,4),1,3,4,"a"),Trial("lineage",F(3,4),2,3,4,"b"),
             Trial("copies",F(3,4),2,2,4,"c"),Trial("copies",F(3,4),3,3,4,"d")]
 def test_improvement(self):self.assertEqual(evaluate(self.rows)["results"]["lineage"]["observed"],"1")
 def test_no_improvement(self):self.assertEqual(evaluate(self.rows)["results"]["copies"]["observed"],"0")
 def test_brier_good(self):self.assertEqual(evaluate(self.rows)["results"]["lineage"]["brier"],"1/16")
 def test_brier_bad(self):self.assertEqual(evaluate(self.rows)["results"]["copies"]["brier"],"9/16")
 def test_selection(self):self.assertEqual(route(evaluate(self.rows))["proposal"],"lineage")
 def test_no_autolearn(self):self.assertFalse(evaluate(self.rows)["learning_applied"])
 def test_unknown_jane_decision(self):self.assertEqual(evaluate(self.rows)["jane_decision"],"UNDECIDED")
 def test_abstention(self):self.assertEqual(route(evaluate(self.rows[:1]))["status"],"ABSTAIN")
 def test_zero(self):self.assertEqual(route(evaluate([]))["status"],"ABSTAIN")
 def test_deterministic(self):self.assertEqual(evaluate(self.rows),evaluate(self.rows))
 def test_invalid_probability(self):
  with self.assertRaises(ValueError):evaluate([Trial("x",F(2),0,1,1,"a")])
 def test_private(self):
  with self.assertRaises(ValueError):evaluate([Trial("x",F(1,2),0,1,1,"a","gated")])
 def test_duplicate(self):
  with self.assertRaises(ValueError):evaluate(self.rows+[self.rows[0]])
 def test_missing_lineage(self):
  with self.assertRaises(ValueError):evaluate([Trial("x",F(1,2),0,1,1,"")])
 def test_invalid_count(self):
  with self.assertRaises(ValueError):evaluate([Trial("x",F(1,2),3,1,2,"a")])
if __name__=="__main__":unittest.main(verbosity=2)
