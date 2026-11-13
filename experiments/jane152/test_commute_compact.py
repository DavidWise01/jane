import unittest
from commute_compact import Event,compare,demo
def e(i,b,op,key='x',v=0,expect=None):return Event(i,b,op,key,v,expect)
class Tests(unittest.TestCase):
 def test_noncommuting(self):self.assertEqual(demo()['status'],'NONCOMMUTING_BRANCHES')
 def test_ab(self):self.assertEqual(demo()['ab']['terminal']['count'],10)
 def test_ba(self):self.assertEqual(demo()['ba']['terminal']['count'],7)
 def test_disjoint(self):self.assertEqual(compare({'x':2},(e('a','A','add','x',3),),(e('b','B','set','y',1),))['status'],'COMPATIBLE_CONTINUATION_CANDIDATE')
 def test_precondition(self):self.assertEqual(compare({'x':2},(e('a','A','require','x',expect=2),),(e('b','B','add','x',1),))['status'],'ORDER_DEPENDENT_FAILURE')
 def test_no_learn(self):self.assertFalse(demo()['learning_applied'])
 def test_frozen(self):self.assertEqual(demo()['active'],'frozen_parent')
 def test_duplicate(self):
  with self.assertRaises(ValueError):compare({},(e('a','A','add'),),(e('a','B','add'),))
 def test_empty(self):
  with self.assertRaises(ValueError):compare({},(),(e('b','B','add'),))
 def test_deterministic(self):self.assertEqual(demo(),demo())
if __name__=='__main__':unittest.main(verbosity=2)
