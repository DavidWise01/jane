import unittest
from conditions import Condition,Policy,Reading,Monitor,growth,demo
N=Condition('normal','mains','locked');H=Condition('hot','battery','holdover');U=Condition('unknown','battery','holdover')
P={N.key():Policy(20,60000,100),H.key():Policy(100,60000,100)}
def fresh():return Monitor(P,Reading(0,0,N),2)
class Tests(unittest.TestCase):
    def test_nominal(self):self.assertEqual(fresh().observe(Reading(10000,1,N))['status'],'WITHIN_PROFILE')
    def test_changed(self):self.assertEqual(fresh().observe(Reading(10000,1,H))['status'],'CONDITION_CHANGE_ACCEPTED')
    def test_change_uses_worst_rate(self):self.assertEqual(fresh().observe(Reading(10000,1,H))['uncertainty_ms'],3)
    def test_nominal_growth(self):self.assertEqual(fresh().observe(Reading(10000,1,N))['uncertainty_ms'],3)
    def test_small_growth(self):self.assertEqual(growth(20,10),1)
    def test_zero_growth(self):self.assertEqual(growth(0,10000),0)
    def test_million(self):self.assertEqual(growth(100,1000000),100)
    def test_negative_growth(self):
        with self.assertRaises(ValueError):growth(10,-1)
    def test_jump(self):self.assertEqual(fresh().observe(Reading(10000,50,N))['status'],'CLOCK_JUMP')
    def test_jump_no_reset(self):
        m=fresh();m.observe(Reading(10000,50,N));self.assertEqual(m.last.tick_ms,0)
    def test_expired_age(self):self.assertEqual(fresh().observe(Reading(60001,0,N))['status'],'CALIBRATION_EXPIRED')
    def test_expired_uncertainty(self):
        p={N.key():Policy(200,600000,3)}
        self.assertEqual(Monitor(p,Reading(0,0,N),2).observe(Reading(10000,0,N))['status'],'CALIBRATION_EXPIRED')
    def test_unknown(self):self.assertEqual(fresh().observe(Reading(10000,0,U))['status'],'UNKNOWN_CONDITION')
    def test_unknown_requires_recalibration(self):self.assertTrue(fresh().observe(Reading(10000,0,U))['recalibration_required'])
    def test_unknown_does_not_assume_bound(self):
        m=fresh();m.observe(Reading(10000,0,U));self.assertEqual(m.observe(Reading(11000,0,U))['status'],'RECALIBRATION_REQUIRED')
    def test_return_without_calibration(self):
        m=fresh();m.observe(Reading(10000,0,U));self.assertEqual(m.observe(Reading(11000,0,N))['status'],'RECALIBRATION_REQUIRED')
    def test_recalibrate(self):
        m=fresh();m.observe(Reading(10000,0,U));self.assertEqual(m.calibrate(Reading(11000,0,N),4,'a'*64),'RECALIBRATED_WITH_DECLARED_EVIDENCE')
    def test_recalibration_restores(self):
        m=fresh();m.observe(Reading(10000,0,U));m.calibrate(Reading(11000,0,N),4,'a'*64);self.assertTrue(m.observe(Reading(12000,0,N))['accepted'])
    def test_recalibration_requires_digest(self):
        with self.assertRaises(ValueError):fresh().calibrate(Reading(10,0,N),2,'invalid')
    def test_recalibration_requires_known(self):
        with self.assertRaises(ValueError):fresh().calibrate(Reading(10,0,U),2,'a'*64)
    def test_recalibration_requires_monotone(self):
        m=fresh();m.observe(Reading(10000,0,N))
        with self.assertRaises(ValueError):m.calibrate(Reading(9000,0,N),2,'a'*64)
    def test_recalibration_negative_uncertainty(self):
        with self.assertRaises(ValueError):fresh().calibrate(Reading(10,0,N),-1,'a'*64)
    def test_nonmonotone(self):self.assertEqual(fresh().observe(Reading(0,0,N))['status'],'NONMONOTONIC_TIME')
    def test_nonmonotone_rejected(self):self.assertFalse(fresh().observe(Reading(0,0,N))['accepted'])
    def test_chain(self):self.assertEqual(fresh().audit(),'VALID_LOCAL_CHAIN')
    def test_tamper(self):
        m=fresh();m.records[0]['kind']='FORGED';self.assertEqual(m.audit(),'TAMPERED')
    def test_external_head(self):self.assertEqual(fresh().audit('b'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_chain_after_observation(self):
        m=fresh();m.observe(Reading(100,0,N));self.assertEqual(m.audit(),'VALID_LOCAL_CHAIN')
    def test_frozen(self):self.assertEqual(fresh().active,'FROZEN_PARENT')
    def test_demo(self):self.assertFalse(demo()['learning_applied'])
    def test_demo_jump(self):self.assertEqual(demo()['jump']['status'],'CLOCK_JUMP')
    def test_demo_unknown(self):self.assertEqual(demo()['unknown_profile']['status'],'UNKNOWN_CONDITION')
    def test_invalid_condition(self):
        with self.assertRaises(ValueError):Condition('','mains','locked')
    def test_invalid_policy(self):
        with self.assertRaises(ValueError):Policy(-1,200,300)
    def test_invalid_policy_map(self):
        with self.assertRaises(ValueError):Monitor({},Reading(0,0,N))
    def test_missing_baseline_policy(self):
        with self.assertRaises(ValueError):Monitor({H.key():P[H.key()]},Reading(0,0,N))
    def test_negative_initial_uncertainty(self):
        with self.assertRaises(ValueError):Monitor(P,Reading(0,0,N),-1)
    def test_negative_tick(self):
        with self.assertRaises(ValueError):Reading(-1,0,N)
    def test_noninteger_tick(self):
        with self.assertRaises(ValueError):Reading(1.1,0,N)
    def test_offset_is_integer(self):
        with self.assertRaises(ValueError):Reading(10,0.5,N)
    def test_witness_is_not_independent(self):self.assertFalse(demo()['real_clock_authenticated'])
if __name__=='__main__':unittest.main(verbosity=2)