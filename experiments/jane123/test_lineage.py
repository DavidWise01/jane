import unittest
from dataclasses import FrozenInstanceError
from lineage import Ledger,demo
class LedgerTests(unittest.TestCase):
 def test_valid(self):self.assertTrue(demo().verify())
 def test_restored(self):self.assertEqual(demo().state()["active"],"v1")
 def test_history(self):self.assertEqual(demo().state()["events"],7)
 def test_retained(self):self.assertIn("v2",demo().state()["versions"])
 def test_deterministic(self):self.assertEqual(demo().state()["head"],demo().state()["head"])
 def test_chain(self):self.assertEqual(demo().events[1].prev,demo().events[0].hash)
 def test_cannot_activate_without_jane(self):
  with self.assertRaises(ValueError):demo().activate("v1","HIVE")
 def test_cannot_restore_without_jane(self):
  with self.assertRaises(ValueError):demo().restore("v2","HIVE")
 def test_tamper(self):
  d=demo();d._events[0].data["version"]="tampered";self.assertFalse(d.verify())
 def test_event_reorder(self):
  d=demo();d._events[0],d._events[1]=d._events[1],d._events[0];self.assertFalse(d.verify())
 def test_no_delete(self):
  with self.assertRaises(ValueError):demo().append("DELETE",{})
 def test_failed_blocked(self):
  d=Ledger();d.freeze("v1","rule");d.propose("v2","v1","other");d.evaluate("v2",False,"proof")
  with self.assertRaises(ValueError):d.activate("v2","JANE")
 def test_immutable_event(self):
  with self.assertRaises(FrozenInstanceError):demo().events[0].kind="X"
 def test_defensive_data(self):
  d=demo();d.events[0].data["version"]="X";self.assertTrue(d.verify())
 def test_prefix_limit(self):
  d=demo();d._events.pop();self.assertTrue(d.verify()) # external head anchor needed
if __name__=="__main__":unittest.main(verbosity=2)
