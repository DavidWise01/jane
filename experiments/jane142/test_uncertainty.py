import unittest
from uncertainty import Flay,Budget,Case,Probe,demo
def c(i=1,truth=None,parent=True,child=False):
 return Case(str(i),'a',truth,parent,child,5,2,'external:a',f'{i+100:064x}')
class Tests(unittest.TestCase):
 def test_status(self):self.assertEqual(demo()[1]['status'],'HOLD_UNCERTAIN_RISK')
 def test_parent(self):self.assertEqual(demo()[1]['parent_risk'],[12,112])
 def test_child(self):self.assertEqual(demo()[1]['child_risk'],[0,100])
 def test_delta(self):self.assertEqual(demo()[1]['change_interval'],[-112,88])
 def test_unknown(self):self.assertEqual(demo()[1]['unknown_count'],2)
 def test_probe(self):self.assertEqual(demo()[1]['next_probe'],'C0')
 def test_score(self):self.assertEqual(demo()[1]['probe_score'],'25')
 def test_no_learning(self):self.assertFalse(demo()[1]['learning_applied'])
 def test_no_activation(self):self.assertEqual(demo()[1]['active'],'frozen_parent')
 def test_chain(self):self.assertEqual(demo()[0].audit(),'VALID_LOCAL_CHAIN')
 def test_determinism(self):self.assertEqual(demo()[1],demo()[1])
 def test_known_only(self):
  f=Flay(Budget(20,(('a',20),)))
  self.assertEqual(f.evaluate([c(1,True,False,True),c(2,True,False,True)])['status'],'JANE_REVIEW_CANDIDATE')
 def test_bad_duplicate(self):
  with self.assertRaises(ValueError):Flay(Budget(20,(('a',20),))).evaluate([c(1),c(1)])
 def test_leak(self):
  f=Flay(Budget(20,(('a',20),)));self.assertEqual(f.evaluate([c(1),c(2)],training_hashes=[c(1).content_hash])['status'],'HOLDOUT_LEAKAGE')
 def test_unknown_same_prediction(self):
  f=Flay(Budget(20,(('a',20),)))
  self.assertEqual(f.evaluate([c(1,parent=True,child=True),c(2,parent=True,child=True)])['change_interval'],[0,0])
if __name__=='__main__':unittest.main(verbosity=2)
