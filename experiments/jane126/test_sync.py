import unittest
from dataclasses import replace
from sync import Chronos,Witness,compare,demo
class Tests(unittest.TestCase):
 def setUp(self):
  self.c=Chronos(2026,11,11,9,44,0,'+',123,45,56,-360)
  self.d=replace(self.c,minute=45,arcminute=46,arcsecond=0)
  self.a=Witness('a','github','g','owned','a'*64,self.c,True)
  self.b=Witness('b','0root.ai','w','owned','a'*64,self.d,True)
  self.x=Witness('x','internet','paper','external','b'*64,self.c,True)
 def test_format(self):self.assertEqual(self.c.stamp(),'{{ - 2026:11:11 || 09:44:00 || +123.45.56 || }}')
 def test_mirror(self):self.assertEqual(compare(self.a,self.b)['status'],'SHARED_RECORDED_ANCESTRY')
 def test_shift(self):self.assertFalse(compare(self.a,self.b)['coordinates_close'])
 def test_delta(self):self.assertEqual(compare(self.a,self.b)['delta_seconds'],60)
 def test_angle(self):self.assertEqual(compare(self.a,self.b)['delta_arcseconds'],4)
 def test_tolerance(self):self.assertTrue(compare(self.a,self.b,60,4)['coordinates_close'])
 def test_outside(self):self.assertEqual(compare(self.a,self.x)['status'],'SEPARATE_DECLARED_ROOTS_REVIEW')
 def test_unknown(self):self.assertEqual(compare(self.a,replace(self.x,ancestry=None))['status'],'UNKNOWN_ANCESTRY')
 def test_shared_custody(self):self.assertEqual(compare(self.a,replace(self.x,custody='owned'))['status'],'SHARED_CUSTODY')
 def test_unverified(self):self.assertEqual(compare(self.a,replace(self.x,attested=False))['status'],'CUSTODY_UNVERIFIED')
 def test_not_learning(self):self.assertFalse(compare(self.a,self.x)['learning_applied'])
 def test_deterministic(self):self.assertEqual(demo(),demo())
 def test_utc_offset(self):self.assertEqual(self.c.seconds(),replace(self.c,hour=15,offset_minutes=0).seconds())
 def test_bad_date(self):
  with self.assertRaises(ValueError):replace(self.c,day=31)
 def test_bad_angle(self):
  with self.assertRaises(ValueError):replace(self.c,arcsecond=60)
 def test_duplicate_identity(self):
  with self.assertRaises(ValueError):compare(self.a,replace(self.b,id='a'))
if __name__=='__main__':unittest.main(verbosity=2)
