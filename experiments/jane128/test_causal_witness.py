import unittest
from causal_witness import Chronos,Event,Edge,inspect
def t(s):return Chronos(2026,11,11,14,0,s,'+',123,45,56,-360)
def e(name,s):return Event(name,t(s))
def link(a='A',b='B',kind='dependency',ancestry='owned:canonical'):return Edge(a,b,kind,'w',ancestry,'a'*64)
class Tests(unittest.TestCase):
 def test_literal(self):self.assertEqual(t(10).stamp(),'{{ - 2026:11:11 || 14:00:10 || +123.45.56 || }}')
 def test_dependency(self):self.assertEqual(inspect([e('A',10),e('B',20)],[link()])['checks'][0]['verdict'],'RECORDED_DEPENDENCY')
 def test_causal_claim(self):self.assertEqual(inspect([e('A',10),e('B',20)],[link(kind='causal_claim')])['checks'][0]['verdict'],'CAUSAL_CLAIM_REVIEW')
 def test_cycle(self):self.assertEqual(inspect([e('A',10),e('B',20)],[link(),link('B','A')])['status'],'CYCLE_REJECTED')
 def test_reverse(self):self.assertEqual(inspect([e('A',20),e('B',10)],[link()])['status'],'CONTRADICTION_REVIEW')
 def test_unknown(self):self.assertEqual(inspect([e('A',10),e('B',20)],[link(ancestry=None)])['status'],'EVIDENCE_INCOMPLETE')
 def test_no_learning(self):self.assertFalse(inspect([],[])['learning_applied'])
 def test_duplicate(self):
  with self.assertRaises(ValueError):inspect([e('A',10),e('A',20)],[])
if __name__=='__main__':unittest.main(verbosity=2)
