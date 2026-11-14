import unittest
from compact import *
class TestCalibration(unittest.TestCase):
 def setUp(self):self.keys,self.pubs,self.t,self.refs=fixture()
 def run_cal(self,refs=None,target=None):return evaluate(self.t if target is None else target,self.refs if refs is None else refs,self.pubs)
 def test_good(self):self.assertEqual(self.run_cal()['status'],'CALIBRATION_CONSISTENT_FIXTURE')
 def test_overlap(self):self.assertEqual(self.run_cal()['overlap'],[995,1008])
 def test_no_real_world_claim(self):self.assertFalse(self.run_cal()['physical_time_verified'])
 def test_no_tightening(self):self.assertFalse(self.run_cal()['uncertainty_tightened'])
 def test_frozen(self):self.assertEqual(self.run_cal()['active_parent'],'FROZEN')
 def test_missing(self):self.assertEqual(self.run_cal(refs=self.refs[:2])['status'],'INSUFFICIENT_DISTINCT_REFERENCES')
 def test_forged_target(self):
  q=dict(self.t);q['payload']=dict(q['payload'],low=0)
  self.assertEqual(self.run_cal(target=q)['status'],'UNTRUSTED_CLOCK_CLAIM')
 def test_forged_reference(self):
  q=dict(self.refs[2]);q['payload']=dict(q['payload'],high=9999)
  self.assertEqual(self.run_cal(refs=[*self.refs[:2],q])['status'],'INSUFFICIENT_DISTINCT_REFERENCES')
 def test_disagreement(self):
  q=sign(Claim('C','root-C','admin-C',2000,2010,100,'new'),self.keys['C'])
  self.assertEqual(self.run_cal(refs=[*self.refs[:2],q])['status'],'REFERENCE_CONFLICT')
 def test_shared_root(self):
  q=sign(Claim('C','root-A','admin-C',990,1008,100,'new'),self.keys['C'])
  self.assertEqual(self.run_cal(refs=[*self.refs[:2],q])['status'],'INSUFFICIENT_DISTINCT_REFERENCES')
 def test_shared_admin(self):
  q=sign(Claim('C','root-C','admin-A',990,1008,100,'new'),self.keys['C'])
  self.assertEqual(self.run_cal(refs=[*self.refs[:2],q])['status'],'INSUFFICIENT_DISTINCT_REFERENCES')
 def test_bad_clock(self):self.assertEqual(self.run_cal(target={})['status'],'UNTRUSTED_CLOCK_CLAIM')
if __name__=='__main__': unittest.main()
