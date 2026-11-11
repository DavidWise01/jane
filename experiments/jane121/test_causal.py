import unittest
from causal import Case, old_rule, revised_rule, evaluate, demonstration
class TestJane121(unittest.TestCase):
 def test_mirror(self):self.assertFalse(revised_rule(Case('a',('x','y'),('r','r'),False,'g')))
 def test_old_wrong(self):self.assertTrue(old_rule(Case('a',('x','y'),('r','r'),False,'g')))
 def test_independent(self):self.assertTrue(revised_rule(Case('a',('x','y'),('r','s'),True,'g')))
 def test_unknown(self):self.assertIsNone(revised_rule(Case('a',('x','y'),('r',None),False,'g')))
 def test_demo_old(self):self.assertEqual(demonstration()['baseline_correct'],1)
 def test_demo_new(self):self.assertEqual(demonstration()['revised_correct'],4)
 def test_gain(self):self.assertEqual(demonstration()['paired_gain'],3)
 def test_review(self):self.assertEqual(demonstration()['status'],'JANE_REVIEW_CANDIDATE')
 def test_no_learning(self):self.assertFalse(demonstration()['learning_applied'])
 def test_digest(self):self.assertEqual(demonstration(),demonstration())
 def test_duplicate(self):
  c=Case('a',('a',),('a',),False,'g')
  with self.assertRaises(ValueError):evaluate([c,c])
 def test_training_rejected(self):
  with self.assertRaises(ValueError):evaluate([Case('a',('a',),('a',),False,'g','train')])
 def test_empty(self):
  with self.assertRaises(ValueError):evaluate([])
 def test_abstain(self):
  a=Case('a',('a','b'),('x',None),False,'one');b=Case('b',('a','b'),('x','y'),True,'two')
  self.assertEqual(evaluate([a,b])['status'],'FLAY_MORE_EVIDENCE')
 def test_single_group(self):
  a=Case('a',('a','b'),('x','x'),False,'one')
  self.assertEqual(evaluate([a])['status'],'FLAY_MORE_EVIDENCE')
if __name__=='__main__':unittest.main(verbosity=2)
