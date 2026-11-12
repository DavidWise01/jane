import unittest
from dataclasses import replace
from flay_coordinate import *
STAMP="{{ 2026.11.12 }}{{ 07.18.00 }}{{ 123.45.56 }}{{ center }}"
class Tests(unittest.TestCase):
 def setUp(self):
  self.c=Coordinate.parse(STAMP,-360);self.o=Observation("question","ancestry",self.c,"github","wrong-root","a"*64)
 def test_nine(self):self.assertEqual(len(ANCHORS),9)
 def test_roundtrip(self):self.assertEqual(self.c.render(),STAMP)
 def test_utc(self):self.assertEqual(self.c.utc(),"2026-11-12T13:18:00+00:00")
 def test_center(self):self.assertEqual(self.c.xyz(),(0,0,0))
 def test_upperrear(self):self.assertEqual(replace(self.c,anchor="upperleftrear").xyz(),(-1,1,-1))
 def test_lowerfront(self):self.assertEqual(replace(self.c,anchor="lowerrightfront").xyz(),(1,-1,1))
 def test_no_bad_date(self):
  with self.assertRaises(ValueError):replace(self.c,day=31)
 def test_no_bad_angle(self):
  with self.assertRaises(ValueError):replace(self.c,arcsecond=60)
 def test_mirrors(self):self.assertEqual(self.o.packet()["ancestry"],replace(self.o,surface="0root.ai").packet()["ancestry"])
 def test_external_unknown(self):self.assertEqual(replace(self.o,surface="internet",source_root=None).packet()["state"],"REQUEST_ANCESTRY")
 def test_no_learn(self):self.assertFalse(self.o.packet()["learning_applied"])
 def test_chain(self):
  l=Ledger();l.append(self.o);self.assertEqual(l.verify(),"VALID_LOCAL_CHAIN")
 def test_external_anchor(self):
  l=Ledger();l.append(self.o);self.assertEqual(l.verify("0"*64),"EXTERNAL_HEAD_MISMATCH")
 def test_tamper(self):
  l=Ledger();l.append(self.o);l.events[0]["packet"]["question"]="evil";self.assertEqual(l.verify(),"TAMPERED")
if __name__=="__main__":unittest.main(verbosity=2)
