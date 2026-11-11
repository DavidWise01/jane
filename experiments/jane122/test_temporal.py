import unittest
from dataclasses import FrozenInstanceError
from temporal import Observation,freeze_rule,assess,demonstration
def o(name,time,truth=False,new=False,cohort='a'):
    return Observation(name,cohort,time,truth,True,new,'origin')
class Tests(unittest.TestCase):
    def test_demo_drift(self):self.assertEqual(demonstration()['status'],'DRIFT_CANDIDATE')
    def test_demo_matched(self):self.assertEqual(demonstration()['matched_count'],3)
    def test_demo_gain(self):self.assertEqual([p['paired_gain'] for p in demonstration()['periods']],[2,0])
    def test_no_autolearn(self):self.assertFalse(demonstration()['learning_applied'])
    def test_pending(self):self.assertEqual(demonstration()['jane_decision'],'UNDECIDED')
    def test_frozen(self):
        f=freeze_rule('v',0,'rule')
        with self.assertRaises(FrozenInstanceError):f.version='x'
    def test_stable(self):self.assertEqual(assess(freeze_rule('v',0,'r'),[o('a',0),o('b',0),o('a',1),o('b',1)])['status'],'STABLE_ON_MATCHED_CASES')
    def test_missing_time(self):self.assertEqual(assess(freeze_rule('v',0,'r'),[o('a',0)])['status'],'INSUFFICIENT_PERIODS')
    def test_duplicate(self):
        with self.assertRaises(ValueError):assess(freeze_rule('v',0,'r'),[o('a',0),o('a',0)])
    def test_unmatched(self):self.assertEqual(assess(freeze_rule('v',0,'r'),[o('a',0),o('b',1)])['status'],'INSUFFICIENT_MATCHED_CASES')
    def test_deterministic(self):self.assertEqual(demonstration(),demonstration())
    def test_digest(self):self.assertEqual(len(demonstration()['digest']),64)
if __name__=='__main__':unittest.main(verbosity=2)
