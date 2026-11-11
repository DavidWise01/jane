import unittest
from dataclasses import replace
from checkpoints import Event,Witness,append,verify,chain_valid,demo
def fixture():
 e=()
 for x in ("freeze","pass","propose","activate","fail","restore"):e=append(e,x)
 h=e[-1].hash
 return e,(Witness("owned","x",5,h,"github"),Witness("a","A",5,h),Witness("b","B",5,h))
class Tests(unittest.TestCase):
 def test_valid(self):self.assertTrue(chain_valid(fixture()[0]))
 def test_match(self):self.assertEqual(verify(*fixture())["status"],"THREE_WITNESS_MATCH")
 def test_truncation(self):
  e,w=fixture();self.assertTrue(chain_valid(e[:-2]));self.assertEqual(verify(e[:-2],w)["status"],"TRUNCATION_SUSPECTED")
 def test_mirrors(self):self.assertEqual(demo()["mirrors"]["status"],"INSUFFICIENT_INDEPENDENT_WITNESSES")
 def test_missing(self):
  e,w=fixture();self.assertEqual(verify(e,w[:2])["status"],"INSUFFICIENT_INDEPENDENT_WITNESSES")
 def test_unknown(self):
  e,w=fixture();self.assertEqual(verify(e,(w[0],w[1],replace(w[2],ancestry=None)))["status"],"INSUFFICIENT_INDEPENDENT_WITNESSES")
 def test_fork(self):
  e,w=fixture();self.assertEqual(verify(e,(w[0],w[1],replace(w[2],head="f"*64)))["status"],"FORK_OR_TAMPER_SUSPECTED")
 def test_chain_tamper(self):
  e,w=fixture();e=e[:2]+(replace(e[2],text="bad"),)+e[3:];self.assertEqual(verify(e,w)["status"],"CHAIN_TAMPERED")
 def test_duplicate_id(self):
  e,w=fixture();self.assertEqual(verify(e,w+(w[0],))["status"],"WITNESS_CONFLICT")
 def test_conflicting_ancestry(self):
  e,w=fixture();self.assertEqual(verify(e,w+(Witness("other","A",3,"a"*64),))["status"],"WITNESS_CONFLICT")
 def test_no_learn(self):self.assertFalse(verify(*fixture())["learning_applied"])
 def test_decision(self):self.assertEqual(verify(*fixture())["jane_decision"],"UNDECIDED")
 def test_deterministic(self):self.assertEqual(demo(),demo())
 def test_stale(self):
  e,w=fixture();self.assertEqual(verify(e,(w[0],w[1],replace(w[2],seq=3)))["status"],"INSUFFICIENT_INDEPENDENT_WITNESSES")
 def test_budget(self):
  e,w=fixture()
  with self.assertRaises(ValueError):verify(e,w*6)
 def test_empty(self):self.assertTrue(chain_valid(()))
if __name__=="__main__":unittest.main(verbosity=2)
