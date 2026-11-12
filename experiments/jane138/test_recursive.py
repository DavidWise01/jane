import unittest
from dataclasses import replace
from recursive import *
class Tests(unittest.TestCase):
 def test_nine(self):self.assertEqual(len(ANCHORS),9)
 def test_unique(self):self.assertEqual(len(set(ANCHORS.values())),9)
 def test_valid(self):self.assertEqual(demo().verify(),'VALID')
 def test_four_cells(self):self.assertEqual(len(demo().cells),4)
 def test_no_new_witness(self):self.assertEqual(demo().packet(('center',))['independent_witness_increment'],0)
 def test_inheritance(self):
  m=demo();self.assertEqual(m.cells[()].source_root,m.cells[('center',)].source_root)
 def test_duplicate(self):
  m=demo()
  with self.assertRaises(ValueError):m.grow((),'center')
 def test_tamper(self):
  m=demo();m.events[0]['head']='0'*64;self.assertEqual(m.verify(),'TAMPERED')
 def test_anchor(self):self.assertEqual(demo().verify('f'*64),'EXTERNAL_HEAD_MISMATCH')
 def test_no_learning(self):self.assertFalse(demo().packet(('center',))['learning_applied'])
if __name__=='__main__':unittest.main(verbosity=2)
