import unittest
from fractions import Fraction
from confounder import Observation,evaluate,demo
T="{{ - 2026:11:11 || 15:18:00 || +123.45.56 || }}"
def o(i,a,b,c="x",root="owned",custody="owned"):
    return Observation(i,a,b,c,T,root,custody)
class Tests(unittest.TestCase):
 def test_reversal(self):self.assertEqual(demo()["status"],"SIMPSON_REVERSAL")
 def test_raw(self):self.assertEqual(Fraction(demo()["raw_difference"]),Fraction(23,50))
 def test_adjusted(self):self.assertEqual(Fraction(demo()["adjusted_difference"]),Fraction(-1,10))
 def test_count(self):self.assertEqual(demo()["n"],200)
 def test_group_count(self):self.assertEqual(len(demo()["strata"]),2)
 def test_no_learning(self):self.assertFalse(demo()["learning_applied"])
 def test_deterministic(self):self.assertEqual(demo(),demo())
 def test_unknown(self):self.assertEqual(evaluate([o("a",True,True,None),o("b",False,False)])["status"],"EVIDENCE_INCOMPLETE")
 def test_missing_root(self):self.assertEqual(evaluate([o("a",True,True,root=None),o("b",False,False)])["status"],"EVIDENCE_INCOMPLETE")
 def test_positivity(self):self.assertEqual(evaluate([o("a",True,True,"x"),o("b",False,False,"y")])["status"],"POSITIVITY_GAP")
 def test_duplicate(self):
  with self.assertRaises(ValueError):evaluate([o("a",True,True),o("a",False,False)])
 def test_empty(self):
  with self.assertRaises(ValueError):evaluate([])
if __name__=="__main__":unittest.main(verbosity=2)
