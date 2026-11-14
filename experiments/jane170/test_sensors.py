import unittest,tempfile
from pathlib import Path
from copy import deepcopy
from sensors import SensorAudit, Policy, fixture, sample, sign, claim, demo

class TestSensors(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.priv,self.keys=fixture()
        self.db=Path(self.tmp.name)/'test.db';self.audit=SensorAudit(self.db,self.keys)
    def tearDown(self):self.audit.close();self.tmp.cleanup()
    def check(self,packets,now=1000000,**kwargs):return self.audit.check(packets,now,**kwargs)
    def test_good(self):self.assertEqual(self.check(sample(self.priv))['status'],'CONDITION_SUPPORTED_FIXTURE')
    def test_good_drift(self):self.assertEqual(self.check(sample(self.priv))['allowed_drift_ppm'],10)
    def test_hot_drift(self):self.assertEqual(self.check(sample(self.priv,('hot_battery',)*3))['allowed_drift_ppm'],120)
    def test_holdover_drift(self):self.assertEqual(self.check(sample(self.priv,('holdover',)*3))['allowed_drift_ppm'],250)
    def test_conflict(self):self.assertEqual(self.check(sample(self.priv,('normal','hot_battery','normal')))['status'],'SENSOR_CONFLICT')
    def test_conflict_no_drift(self):self.assertIsNone(self.check(sample(self.priv,('normal','hot_battery','normal')))['allowed_drift_ppm'])
    def test_missing(self):self.assertEqual(self.check(sample(self.priv)[:2])['status'],'INSUFFICIENT_PROVENANCE')
    def test_missing_no_drift(self):self.assertIsNone(self.check(sample(self.priv)[:2])['allowed_drift_ppm'])
    def test_unknown(self):self.assertEqual(self.check(sample(self.priv,('mystery',)*3))['status'],'UNKNOWN_CONDITION')
    def test_unknown_no_drift(self):self.assertIsNone(self.check(sample(self.priv,('mystery',)*3))['allowed_drift_ppm'])
    def test_profile_changed(self):self.assertEqual(self.check(sample(self.priv),expected_condition='hot_battery')['status'],'PROFILE_CHANGED')
    def test_profile_changed_no_drift(self):self.assertIsNone(self.check(sample(self.priv),expected_condition='holdover')['allowed_drift_ppm'])
    def test_bad_signature(self):
        p=sample(self.priv);p[0]['claim']['condition']='hot_battery';r=self.check(p);self.assertIn('BAD_SIGNATURE',[x['reason'] for x in r['rejections']])
    def test_invalid_signature_hex(self):
        p=sample(self.priv);p[0]['signature']='??';r=self.check(p);self.assertIn('BAD_SIGNATURE',[x['reason'] for x in r['rejections']])
    def test_wrong_signer(self):
        p=sample(self.priv);p[0]['signature']=self.priv[1].sign(__import__('sensors').canonical(p[0]['claim'])).hex();r=self.check(p);self.assertIn('BAD_SIGNATURE',[x['reason'] for x in r['rejections']])
    def test_identity_tamper(self):
        p=sample(self.priv);p[0]['claim']['root']='evil';r=self.check(p);self.assertIn('IDENTITY_MISMATCH',[x['reason'] for x in r['rejections']])
    def test_unknown_sensor(self):
        p=sample(self.priv);p[0]['claim']['sensor']='unknown';r=self.check(p);self.assertIn('UNKNOWN_SENSOR',[x['reason'] for x in r['rejections']])
    def test_bad_domain(self):
        p=sample(self.priv);p[0]['claim']['domain']='other';r=self.check(p);self.assertIn('BAD_DOMAIN',[x['reason'] for x in r['rejections']])
    def test_old(self):
        p=sample(self.priv,now_ms=0);r=self.check(p);self.assertIn('STALE_OBSERVATION',[x['reason'] for x in r['rejections']])
    def test_future(self):
        p=sample(self.priv,now_ms=1200000);r=self.check(p);self.assertIn('FUTURE_OBSERVATION',[x['reason'] for x in r['rejections']])
    def test_future_within(self):
        p=sample(self.priv,now_ms=1020000);self.assertEqual(self.check(p)['status'],'CONDITION_SUPPORTED_FIXTURE')
    def test_uncertainty_excess(self):
        p=sample(self.priv);p[0]=sign(self.priv[0],{**p[0]['claim'],'uncertainty_ms':10001});r=self.check(p);self.assertIn('UNSUPPORTED_UNCERTAINTY',[x['reason'] for x in r['rejections']])
    def test_negative_uncertainty(self):
        p=sample(self.priv);p[0]=sign(self.priv[0],{**p[0]['claim'],'uncertainty_ms':-1});r=self.check(p);self.assertIn('UNSUPPORTED_UNCERTAINTY',[x['reason'] for x in r['rejections']])
    def test_fractional_time(self):
        p=sample(self.priv);p[0]=sign(self.priv[0],{**p[0]['claim'],'observed_ms':1.5});r=self.check(p);self.assertIn('MALFORMED_TIME',[x['reason'] for x in r['rejections']])
    def test_nonce_empty(self):
        p=sample(self.priv);p[0]=sign(self.priv[0],{**p[0]['claim'],'nonce':''});r=self.check(p);self.assertIn('BAD_NONCE',[x['reason'] for x in r['rejections']])
    def test_replay(self):
        p=sample(self.priv);self.check(p);r=self.check(p);self.assertEqual(len([x for x in r['rejections'] if x['reason']=='REPLAY']),3)
    def test_replay_restart(self):
        p=sample(self.priv);self.check(p);self.audit.close();self.audit=SensorAudit(self.db,self.keys);r=self.check(p);self.assertEqual(r['status'],'INSUFFICIENT_PROVENANCE')
    def test_replay_within_batch(self):
        p=sample(self.priv);r=self.check([p[0],deepcopy(p[0]),p[1],p[2]]);self.assertIn('REPLAY',[x['reason'] for x in r['rejections']])
    def test_duplicate_root(self):
        pub,r,a=self.keys['sensor2'];self.keys['sensor2']=(pub,'root1',a)
        p=sample(self.priv);p[1]=sign(self.priv[1],{**p[1]['claim'],'root':'root1'})
        self.assertIn('SHARED_CUSTODY_ROOT',[x['reason'] for x in self.check(p)['rejections']])
    def test_duplicate_admin(self):
        pub,r,a=self.keys['sensor2'];self.keys['sensor2']=(pub,r,'admin1')
        p=sample(self.priv);p[1]=sign(self.priv[1],{**p[1]['claim'],'admin':'admin1'})
        self.assertIn('SHARED_ADMINISTRATION',[x['reason'] for x in self.check(p)['rejections']])
    def test_ledger(self):self.check(sample(self.priv));self.assertEqual(self.audit.ledger(),'VALID_LOCAL_CHAIN')
    def test_ledger_tamper(self):
        self.check(sample(self.priv));self.audit.db.execute("UPDATE events SET kind='TAMPER' WHERE seq=1");self.audit.db.commit();self.assertEqual(self.audit.ledger(),'TAMPERED')
    def test_audit_no_learn(self):self.assertFalse(self.check(sample(self.priv))['learning_applied'])
    def test_audit_frozen(self):self.assertEqual(self.check(sample(self.priv))['parent'],'frozen_parent')
    def test_not_physically_verified(self):self.assertFalse(self.check(sample(self.priv))['physical_condition_verified'])
    def test_not_independent_verified(self):self.assertFalse(self.check(sample(self.priv))['independent_operators_verified'])
    def test_recalibrate_conflict(self):self.assertTrue(self.check(sample(self.priv,('normal','hot_battery','normal')))['recalibration_required'])
    def test_recalibrate_unknown(self):self.assertTrue(self.check(sample(self.priv,('mystery',)*3))['recalibration_required'])
    def test_recalibrate_good(self):self.assertFalse(self.check(sample(self.priv))['recalibration_required'])
    def test_policy_validation(self):
        with self.assertRaises(ValueError):Policy(max_age_ms=-1)
    def test_policy_quorum(self):
        with self.assertRaises(ValueError):Policy(min_roots=0)
    def test_non_integer_now(self):
        with self.assertRaises(ValueError):self.check(sample(self.priv),now=1.5)
    def test_no_packets(self):self.assertEqual(self.check([])['status'],'INSUFFICIENT_PROVENANCE')
    def test_demo(self):self.assertEqual(demo()['ledger'],'VALID_LOCAL_CHAIN')
    def test_demo_conflict(self):self.assertEqual(demo()['conflict']['status'],'SENSOR_CONFLICT')
    def test_demo_unknown(self):self.assertEqual(demo()['unknown']['status'],'UNKNOWN_CONDITION')
if __name__=='__main__':unittest.main(verbosity=2)