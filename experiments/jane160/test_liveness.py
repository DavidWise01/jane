import unittest
from liveness import Edge,System,fixture,intermittent_fixture,hash_obj

class Tests(unittest.TestCase):
 def test_possible(self):self.assertEqual(fixture().analyze('none')['status'],'POSSIBLE_NOT_INEVITABLE')
 def test_weak(self):self.assertEqual(fixture().analyze('weak')['status'],'PROGRESS_UNDER_WEAK_FAIRNESS')
 def test_strong(self):self.assertEqual(fixture().analyze('strong')['status'],'PROGRESS_UNDER_STRONG_FAIRNESS')
 def test_intermittent_none(self):self.assertEqual(intermittent_fixture().analyze('none')['status'],'POSSIBLE_NOT_INEVITABLE')
 def test_intermittent_weak(self):self.assertEqual(intermittent_fixture().analyze('weak')['status'],'POSSIBLE_NOT_INEVITABLE')
 def test_intermittent_strong(self):self.assertEqual(intermittent_fixture().analyze('strong')['status'],'PROGRESS_UNDER_STRONG_FAIRNESS')
 def test_shortest(self):self.assertEqual(len(fixture().analyze()['progress_path']),1)
 def test_cycle(self):self.assertEqual(len(fixture().analyze()['nonprogress_lasso']['cycle']),1)
 def test_intermit_cycle(self):self.assertEqual(len(intermittent_fixture().analyze('weak')['nonprogress_lasso']['cycle']),2)
 def test_guaranteed(self):
  s=System(['a','b'],[Edge('a','next','b'),Edge('b','stay','b')],'a',['b'])
  self.assertEqual(s.analyze()['status'],'GUARANTEED_PROGRESS')
 def test_unreachable(self):
  s=System(['a','b'],[Edge('a','stay','a'),Edge('b','stay','b')],'a',['b'])
  self.assertEqual(s.analyze()['status'],'GOAL_UNREACHABLE')
 def test_bad_fairness(self):
  with self.assertRaises(ValueError):fixture().analyze('magical')
 def test_bad_deadlock(self):
  with self.assertRaises(ValueError):System(['a'],[],'a',['a'])
 def test_bad_edge(self):
  with self.assertRaises(ValueError):System(['a'],[Edge('a','x','outside')],'a',['a'])
 def test_bad_goal(self):
  with self.assertRaises(ValueError):System(['a'],[Edge('a','stay','a')],'a',['b'])
 def test_duplicate_edge(self):
  with self.assertRaises(ValueError):System(['a'],[Edge('a','x','a'),Edge('a','x','a')],'a',['a'])
 def test_budget(self):
  s=System(['a','b'],[Edge('a','go','b'),Edge('b','stay','b')],'a',['b'],budget=1)
  self.assertEqual(s.analyze()['status'],'INCONCLUSIVE_BUDGET')
 def test_frozen(self):self.assertEqual(fixture().analyze()['active'],'frozen_parent')
 def test_not_activated(self):self.assertFalse(fixture().analyze()['learning_applied'])
 def test_no_witness(self):self.assertEqual(fixture().analyze()['independent_witness_increment'],0)
 def test_deterministic(self):self.assertEqual(fixture().analyze()['digest'],fixture().analyze()['digest'])
 def test_digest(self):self.assertEqual(len(fixture().analyze()['digest']),64)
 def test_scope(self):self.assertIn('finite',fixture().analyze()['scope'])
 def test_cycle_only_non_goal(self):self.assertNotIn('goal',fixture().analyze()['nonprogress_lasso']['states'])
 def test_fair_cycle_weak_reject(self):self.assertFalse(fixture().fair_cycle([Edge('s0','stutter','s0')],'weak'))
 def test_fair_cycle_none_accept(self):self.assertTrue(fixture().fair_cycle([Edge('s0','stutter','s0')],'none'))
 def test_fair_cycle_strong_reject(self):self.assertFalse(intermittent_fixture().fair_cycle([Edge('s0','switch','s1'),Edge('s1','switch','s0')],'strong'))
 def test_fair_cycle_weak_accept(self):self.assertTrue(intermittent_fixture().fair_cycle([Edge('s0','switch','s1'),Edge('s1','switch','s0')],'weak'))
 def test_fairness_does_not_change_graph(self):self.assertEqual(fixture().analyze('none')['edges'],fixture().analyze('strong')['edges'])
 def test_target_reachable(self):self.assertEqual(fixture().analyze()['progress_path'][0]['target'],'goal')
 def test_sorted_states(self):self.assertEqual(fixture().analyze()['states'],['goal','s0'])
 def test_invalid_initial(self):
  with self.assertRaises(ValueError):System(['a'],[Edge('a','stay','a')],'unknown',['a'])
 def test_empty_graph(self):
  with self.assertRaises(ValueError):System([],[],'a',[])
 def test_max_states(self):
  with self.assertRaises(ValueError):System([str(i) for i in range(33)],[], '0',['0'])
 def test_max_edges(self):
  with self.assertRaises(ValueError):System(['a'],[Edge('a',str(i),'a') for i in range(129)],'a',['a'])
 def test_single_goal(self):
  s=System(['a'],[Edge('a','stay','a')],'a',['a']);self.assertEqual(s.analyze()['status'],'GUARANTEED_PROGRESS')
 def test_hash_changes(self):self.assertNotEqual(hash_obj({'a':1}),hash_obj({'a':2}))
 def test_cycle_lasso_repeats(self):
  x=intermittent_fixture().analyze('weak')['nonprogress_lasso']; self.assertEqual(x['cycle'][-1]['target'],x['cycle'][0]['source'])
 def test_fairness_declared(self):self.assertEqual(fixture().analyze('strong')['fairness'],'strong')
 def test_all_goal_no_lasso(self):self.assertIsNone(System(['a'],[Edge('a','tick','a')],'a',['a']).analyze()['nonprogress_lasso'])

if __name__=='__main__':unittest.main()