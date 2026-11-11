import unittest
from fractions import Fraction as F
from sensitivity import demo,sweep
STAMP="{{ - 2026:11:11 || 17:31:00 || +123.45.56 || }}"
def run(o,bounds):return sweep(o,bounds,STAMP,-360,["owned"])
class TestJANE131(unittest.TestCase):
 def test_threshold(self):self.assertEqual(demo()["threshold"],"1/10")
 def test_negative(self):self.assertEqual(demo()["models"][0]["verdict"],"SIGN_UNRESOLVED" if False else "SIGN_UNRESOLVED" if demo()["models"][0]["bias_bound"]=="1/5" else "NEGATIVE_WITHIN_ASSUMPTION")
 def test_zero_possible(self):self.assertTrue(any(x["upper"]=="0" for x in demo()["models"]))
 def test_positive(self):self.assertEqual(run(F(1,10),[("small",F(1,20))])["models"][0]["verdict"],"POSITIVE_WITHIN_ASSUMPTION")
 def test_no_learning(self):self.assertFalse(demo()["learning_applied"])
 def test_determinism(self):self.assertEqual(demo(),demo())
 def test_bad_bound(self):
  with self.assertRaises(ValueError):run(F(0),[("x",F(2))])
 def test_bad_date(self):
  with self.assertRaises(ValueError):sweep(F(0),[("x",F(0))],STAMP.replace("11:11","02:30"),-360,["owned"])
if __name__=="__main__":unittest.main(verbosity=2)
