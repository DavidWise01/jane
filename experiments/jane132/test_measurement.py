import unittest
from fractions import Fraction as F
from measurement import Probe,Branch,plan,gain,demo,chronos
T="{{ - 2026:11:11 || 17:31:00 || +123.45.56 || }}"
class Tests(unittest.TestCase):
 def p(self,id="a",cost=2,origin="x",surface="internet",branches=None):
  return Probe(id,cost,origin,"public",branches or (Branch(F(1,2),F(1,20)),Branch(F(1,2),F(1,10))),T,-360,surface)
 def test_chronos(self):self.assertTrue(chronos(T,-360).startswith("2026-11-11T23:31"))
 def test_gain(self):self.assertEqual(gain(self.p(),F(1,5)),F(1,8))
 def test_select(self):self.assertEqual(demo()["selected"],"measure_C")
 def test_budget(self):self.assertEqual(plan((self.p(cost=5),),F(1,5),4)["status"],"ABSTAIN")
 def test_mirror(self):self.assertEqual(self.p(surface="github").root(),self.p(surface="0root.ai").root())
 def test_reused(self):self.assertEqual(plan((self.p(),),F(1,5),4,("x",))["status"],"ABSTAIN")
 def test_no_learn(self):self.assertFalse(demo()["learning_applied"])
 def test_determinism(self):self.assertEqual(demo(),demo())
 def test_bad_prob(self):
  with self.assertRaises(ValueError):gain(self.p(branches=(Branch(F(1,3),F(1,10)),)),F(1,5))
 def test_duplicate(self):
  with self.assertRaises(ValueError):plan((self.p(),self.p()),F(1,5),4)
if __name__=="__main__":unittest.main(verbosity=2)
