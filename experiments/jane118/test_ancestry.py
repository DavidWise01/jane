import unittest
from ancestry import AncestryGraph,Source,GraphError
def g(*items):return AncestryGraph(Source(*x) for x in items)
class RootTests(unittest.TestCase):
    def test_direct(self):self.assertEqual(g(("r",),("a",("r",)),("b",("r",))).compare("a","b")["verdict"],"SHARED_ANCESTRY")
    def test_multigen(self):self.assertEqual(g(("r",),("a",("r",)),("b",("a",)),("c",("r",))).compare("b","c")["shared_roots"],["r"])
    def test_separate(self):self.assertEqual(g(("a",),("b",)).compare("a","b")["verdict"],"SEPARATE_RECORDED_ROOTS")
    def test_missing(self):self.assertEqual(g(("a",("missing",)),("b",)).compare("a","b")["verdict"],"UNKNOWN")
    def test_incomplete(self):self.assertEqual(g(("a",(),False),("b",)).compare("a","b")["verdict"],"UNKNOWN")
    def test_self_cycle(self):self.assertEqual(g(("a",("a",)),).trace("a")["cycles"],["a"])
    def test_cycle(self):self.assertEqual(g(("a",("b",)),("b",("a",))).trace("a")["status"],"UNRESOLVED")
    def test_depth(self):self.assertEqual(g(("r",),("a",("r",)),("b",)).compare("a","b",0)["verdict"],"UNKNOWN")
    def test_depth_exact(self):self.assertEqual(g(("r",),("a",("r",))).trace("a",1)["roots"],["r"])
    def test_negative(self):
        with self.assertRaises(GraphError):g(("a",)).trace("a",-1)
    def test_too_deep(self):
        with self.assertRaises(GraphError):g(("a",)).trace("a",13)
    def test_duplicate(self):
        with self.assertRaises(GraphError):g(("a",),("a",))
    def test_max_nodes(self):
        with self.assertRaises(GraphError):AncestryGraph(Source(str(i)) for i in range(129))
    def test_diamond(self):self.assertEqual(g(("r",),("a",("r",)),("b",("r",)),("top",("a","b"))).trace("top")["roots"],["r"])
    def test_shared_with_unknown(self):
        x=g(("r",),("a",("r","missing")),("b",("r",)))
        self.assertEqual(x.compare("a","b")["verdict"],"SHARED_ANCESTRY")
    def test_jane_gate(self):self.assertFalse(g(("a",),("b",)).compare("a","b")["learning_applied"])
    def test_digest(self):
        x=g(("a",),("b",));self.assertEqual(x.evidence_packet("a","b"),x.evidence_packet("a","b"))
    def test_unknown_start(self):self.assertEqual(g(("a",)).trace("missing")["status"],"UNRESOLVED")
    def test_syndication(self):self.assertEqual(g(("origin",),("publisher",("origin",)),("syndication",("publisher",))).compare("publisher","syndication")["verdict"],"SHARED_ANCESTRY")
    def test_tainted(self):self.assertIn("unrecorded",g(("r",),("a",("r","unrecorded"))).trace("a")["unknown"])
if __name__=="__main__":unittest.main(verbosity=2)
