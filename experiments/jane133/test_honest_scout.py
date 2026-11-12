import unittest
from fractions import Fraction as F
from honest_scout import Ledger,Prediction,Outcome,root,demo
T="{{ - 2026:11:11 || 18:58:00 || +123.45.56 || }}"
def p(id="a"):return Prediction(id,"s",F(3,4),2,T,"github","owned")
def o(id="a",surface="internet",gain=F(1,2),verified=True):return Outcome(id,gain,T,surface,"external",verified)
class Tests(unittest.TestCase):
 def test_mirror(self):self.assertEqual(root("github","x"),root("0root.ai","y"))
 def test_good(self):self.assertEqual(demo()["scouts"]["lineage"]["mean_absolute_error"],"0")
 def test_bad(self):self.assertEqual(demo()["scouts"]["copies"]["status"],"RECALIBRATE")
 def test_no_learning(self):self.assertFalse(demo()["learning_applied"])
 def test_deterministic(self):self.assertEqual(demo(),demo())
 def test_outcome_before_prediction(self):
  with self.assertRaises(ValueError):Ledger().observe(o())
 def test_mirror_not_independent(self):
  l=Ledger();l.predict(p());l.observe(o(surface="0root.ai"));self.assertEqual(l.report()["scouts"]["s"]["verified_count"],0)
 def test_unverified(self):
  l=Ledger();l.predict(p());l.observe(o(verified=False));self.assertEqual(l.report()["scouts"]["s"]["unverified_count"],1)
 def test_duplicate(self):
  l=Ledger();l.predict(p())
  with self.assertRaises(ValueError):l.predict(p())
 def test_pending(self):
  l=Ledger();l.predict(p());self.assertEqual(l.report()["scouts"]["s"]["pending_count"],1)
if __name__=="__main__":unittest.main(verbosity=2)
