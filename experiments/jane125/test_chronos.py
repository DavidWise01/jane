import unittest
from chronos import Chronos,Receipt,verify
S='{{ - 2026:11:11 || 09:44:00 || +123.45.56 || }}'
class Tests(unittest.TestCase):
 def setUp(self):
  self.c=Chronos.parse(S,-360);self.h='a'*64
  self.rs=tuple(Receipt(str(i),str(i),self.h,6,self.c,True) for i in range(3))
 def test_roundtrip(self):self.assertEqual(self.c.render(),S)
 def test_utc(self):self.assertTrue(self.c.instant().startswith('2026-11-11T15:44:00'))
 def test_angle(self):self.assertEqual(self.c.arcseconds(),445556)
 def test_invalid_date(self):
  with self.assertRaises(ValueError):Chronos.parse(S.replace('2026:11:11','2026:02:30'),-360)
 def test_invalid_angle(self):
  with self.assertRaises(ValueError):Chronos.parse(S.replace('123.45.56','123.60.56'),-360)
 def test_three_roots(self):self.assertEqual(verify(self.h,6,self.rs)['status'],'THREE_CUSTODY_ROOT_MATCH')
 def test_truncated(self):self.assertEqual(verify(self.h,4,self.rs)['status'],'TRUNCATION_SUSPECTED')
 def test_two_roots(self):self.assertEqual(verify(self.h,6,self.rs[:2])['status'],'INSUFFICIENT_AUTHENTICATED_CUSTODY')
 def test_no_learning(self):self.assertFalse(verify(self.h,6,self.rs)['learning_applied'])
if __name__=='__main__':unittest.main(verbosity=2)
