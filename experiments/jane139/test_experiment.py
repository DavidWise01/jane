import unittest
from experiment import Experiment,demo,CHRONOS
class Tests(unittest.TestCase):
 def setUp(self):
  self.x=Experiment();self.a=self.x.propose((),"upperleftrear","count_urls");self.b=self.x.propose((),"upperrightfront","root_aware")
  self.cases=[("mirror","holdout",("github","site"),("owned","owned"),False,"owned"),("labs","holdout",("a","b"),("a","b"),True,"labs")]
 def test_demo(self):self.assertEqual(demo()[1]["candidate_correct"],4)
 def test_gain(self):self.assertEqual(demo()[1]["gains"],3)
 def test_parent_immutable(self):self.assertEqual(self.x.cells[()].root,self.a.root)
 def test_chronos(self):self.assertEqual(self.b.chronos,CHRONOS)
 def test_no_new_root(self):self.assertEqual(self.a.root,self.b.root)
 def test_no_activation(self):self.x.compare(self.a.path,self.b.path,self.cases);self.assertEqual(self.x.active,())
 def test_review(self):self.assertEqual(self.x.compare(self.a.path,self.b.path,self.cases)["status"],"JANE_REVIEW_CANDIDATE")
 def test_chain(self):self.assertTrue(self.x.verify())
 def test_collision(self):
  with self.assertRaises(ValueError):self.x.propose((),"upperleftrear","root_aware")
 def test_invalid_rule(self):
  with self.assertRaises(ValueError):self.x.propose((),"center","invalid")
 def test_no_learning(self):self.assertFalse(demo()[1]["learning_applied"])
 def test_bad_split(self):
  with self.assertRaises(ValueError):self.x.compare(self.a.path,self.b.path,[("x","train",("a","b"),("a","b"),True,"test")])
if __name__=="__main__":unittest.main(verbosity=2)
