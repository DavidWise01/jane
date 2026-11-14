import unittest, math
from missingness import Plan,Observation,Audit,fixture,demo,sha
class Tests(unittest.TestCase):
 def run_case(self,statuses,baseline=None):
  p,o=fixture(statuses);a=Audit(p);return a,a.analyze(o,200,baseline)
 def test_demo(self):self.assertEqual(demo()['result']['rounds_total'],8)
 def test_total(self):self.assertEqual(self.run_case(['published','absent','unknown'])[1]['rounds_total'],3)
 def test_denominator(self):self.assertEqual(self.run_case(['published','absent','unknown'])[1]['missing_fraction_all'],1/3)
 def test_missing(self):self.assertEqual(self.run_case(['published','absent','unknown'])[1]['missing'],1)
 def test_unresolved(self):self.assertEqual(self.run_case(['published','absent','unknown'])[1]['unresolved'],1)
 def test_published(self):self.assertEqual(self.run_case(['published','absent','unknown'])[1]['published'],1)
 def test_longest(self):self.assertEqual(self.run_case(['absent','absent','published','absent'])[1]['longest_missing_run'],2)
 def test_no_run(self):self.assertEqual(self.run_case(['published','unknown'])[1]['longest_missing_run'],0)
 def test_outage_unresolved(self):self.assertEqual(self.run_case(['outage'])[1]['unresolved'],1)
 def test_missing_not_intent(self):self.assertFalse(self.run_case(['absent'])[1]['intent_proven'])
 def test_unknown_not_missing(self):self.assertEqual(self.run_case(['unknown'])[1]['missing'],0)
 def test_incomplete_count(self):self.assertEqual(self.run_case(['unknown'])[1]['rows'][0]['status'],'UNKNOWN_INCOMPLETE')
 def test_declared_absence(self):self.assertEqual(self.run_case(['absent'])[1]['rows'][0]['status'],'NOT_OBSERVED_AFTER_DEADLINE')
 def test_published_status(self):self.assertEqual(self.run_case(['published'])[1]['rows'][0]['status'],'PUBLISHED_OBSERVED')
 def test_outage_status(self):self.assertEqual(self.run_case(['outage'])[1]['rows'][0]['status'],'OUTAGE_OR_INCOMPLETE')
 def test_baseline_zero(self):self.assertEqual(self.run_case(['absent'],0)[1]['binomial_upper_tail_resolved'],0)
 def test_baseline_one(self):self.assertEqual(self.run_case(['absent'],1)[1]['binomial_upper_tail_resolved'],1)
 def test_baseline_unknown(self):self.assertIsNone(self.run_case(['unknown'],.5)[1]['binomial_upper_tail_resolved'])
 def test_baseline_tail(self):self.assertAlmostEqual(self.run_case(['absent','published'],.2)[1]['binomial_upper_tail_resolved'],.36)
 def test_deterministic(self):self.assertEqual(demo()['result']['digest'],demo()['result']['digest'])
 def test_frozen(self):self.assertEqual(self.run_case(['absent'])[1]['parent_active'],'frozen')
 def test_no_learning(self):self.assertFalse(self.run_case(['absent'])[1]['learning_applied'])
 def test_no_physical_independence(self):self.assertFalse(self.run_case(['published'])[1]['independent_physical_roots_verified'])
 def test_chain(self):self.assertEqual(self.run_case(['absent'])[0].verify_chain(),'LOCAL_CHAIN_VALID')
 def test_external_head(self):self.assertEqual(self.run_case(['absent'])[0].verify_chain('f'*64),'EXTERNAL_HEAD_MISMATCH')
 def test_tampered_chain(self):
  a,r=self.run_case(['absent']);a.events[0]['kind']='FORGED';self.assertEqual(a.verify_chain(),'LOCAL_CHAIN_INVALID')
 def test_bad_round_order(self):
  with self.assertRaises(ValueError):Plan((42,41),100,('a','b'))
 def test_duplicate_round(self):
  with self.assertRaises(ValueError):Plan((40,40),100,('a','b'))
 def test_empty(self):
  with self.assertRaises(ValueError):Plan((),100,('a','b'))
 def test_duplicate_root(self):
  with self.assertRaises(ValueError):Plan((40,),100,('a','a'))
 def test_bad_quorum(self):
  with self.assertRaises(ValueError):Plan((40,),100,('a','b'),3)
 def test_too_many_rounds(self):
  with self.assertRaises(ValueError):Plan(tuple(range(513)),100,('a','b'))
 def test_invalid_status(self):
  with self.assertRaises(ValueError):Observation(40,'a','unknown',100,'0'*64)
 def test_bad_hash(self):
  with self.assertRaises(ValueError):Observation(40,'a','published',100,'abc')
 def test_unregistered_round(self):
  p,o=fixture(['published']);o.append(Observation(99,'a','absent',120,'a'*64))
  with self.assertRaises(ValueError):Audit(p).analyze(o,200)
 def test_unregistered_root(self):
  p,o=fixture(['unknown']);o.append(Observation(40,'x','absent',120,'a'*64))
  with self.assertRaises(ValueError):Audit(p).analyze(o,200)
 def test_duplicate_observation(self):
  p,o=fixture(['published']);o[1]=o[0]
  with self.assertRaises(ValueError):Audit(p).analyze(o,200)
 def test_bad_baseline(self):
  p,o=fixture(['absent'])
  with self.assertRaises(ValueError):Audit(p).analyze(o,200,-.2)
 def test_nan_baseline(self):
  p,o=fixture(['absent'])
  with self.assertRaises(ValueError):Audit(p).analyze(o,200,float('nan'))
 def test_future_observation_not_counted(self):
  p,o=fixture(['published']);a=Audit(p);self.assertEqual(a.analyze(o,100)['unresolved'],1)
 def test_predeadline_absence_not_counted(self):
  p,o=fixture(['absent']);o=[Observation(x.round,x.observer_root,x.status,99,x.evidence_hash) for x in o];self.assertEqual(Audit(p).analyze(o,200)['missing'],0)
 def test_conflict(self):
  p,o=fixture(['published'],('a','b','c','d'));o=[Observation(x.round,x.observer_root,'absent' if x.observer_root in ('c','d') else 'published',120,x.evidence_hash) for x in o];a=Audit(Plan(p.rounds,p.deadline_ms,p.observer_roots,2));self.assertEqual(a.analyze(o,200)['rows'][0]['status'],'CONFLICTING_OBSERVATIONS')
 def test_missing_challenges_not_evidence(self):self.assertEqual(self.run_case(['unknown','unknown','absent'])[1]['missing_fraction_all'],1/3)
 def test_plan_digest(self):self.assertEqual(len(demo()['result']['plan_digest']),64)
 def test_result_digest(self):self.assertEqual(len(demo()['result']['digest']),64)
 def test_three_root_fixture(self):self.assertEqual(self.run_case(['published'])[1]['rows'][0]['published'],3)
 def test_budget(self):
  p,o=fixture(['published']);o.append(o[0]);
  with self.assertRaises(ValueError):Audit(p).analyze(o,200)
if __name__=='__main__':unittest.main(verbosity=2)