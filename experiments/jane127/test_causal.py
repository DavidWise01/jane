import unittest
from dataclasses import replace
from causal import Chronos,Estimate,Report,order,compare,demo
def c(s):return Chronos(2026,11,11,14,0,s,'+',123,45,56,-360)
def r(i,s,root='r',custody='c'):return Report(i,'E',None,Estimate(c(s)),Estimate(c(s+1)),root,custody)
class Tests(unittest.TestCase):
 def test_coordinate(self):self.assertEqual(c(10).render(),'{{ - 2026:11:11 || 14:00:10 || +123.45.56 || }}')
 def test_observation(self):self.assertEqual(compare(r('a',10),r('b',15))['observation_order'],'A_BEFORE_B')
 def test_receipt(self):self.assertEqual(compare(r('a',10),r('b',15))['receipt_order'],'A_BEFORE_B')
 def test_no_causal_leap(self):self.assertEqual(demo()['event_order'],'EVENT_TIME_UNKNOWN')
 def test_uncertainty(self):self.assertEqual(order(Estimate(c(10),5),Estimate(c(15),5)),'ORDER_UNRESOLVED')
 def test_reverse(self):self.assertEqual(order(Estimate(c(20)),Estimate(c(10))),'B_BEFORE_A')
 def test_explicit_events(self):
  a=replace(r('a',10),event=Estimate(c(5)));b=replace(r('b',15),event=Estimate(c(2)))
  self.assertEqual(compare(a,b)['event_order'],'B_BEFORE_A')
 def test_same_root(self):self.assertEqual(compare(r('a',10),r('b',15))['ancestry'],'SHARED')
 def test_unknown_root(self):self.assertEqual(compare(r('a',10,None),r('b',15))['ancestry'],'UNKNOWN')
 def test_duplicate_id(self):
  with self.assertRaises(ValueError):compare(r('a',10),r('a',15))
 def test_no_learning(self):self.assertFalse(demo()['learning_applied'])
 def test_digest(self):self.assertEqual(demo(),demo())
if __name__=='__main__':unittest.main(verbosity=2)
