import copy
import os
import tempfile
import unittest
from stimulus_pattern import FLAY217, fixture, signed, digest, run_demo

class Test217(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.gate=FLAY217(os.path.join(self.tmp.name,'db'))
        self.parts=list(fixture(bytes.fromhex('ab'*32)))
    def tearDown(self):
        self.gate.close();self.tmp.cleanup()
    def change(self,idx,**updates):
        self.parts[idx]=signed(self.parts[6][('plan','commitment','reveal','response')[idx]], dict(self.parts[idx]['body'],**updates))
    def check(self):return self.gate.evaluate(*self.parts[:6]).status
    def test_valid(self):self.assertEqual(self.check(),'CHALLENGE_RESPONSE_CONSISTENT_FIXTURE')
    def test_replay(self):self.check();self.assertEqual(self.check(),'REPLAY')
    def test_replay_restart(self):
        self.check();self.gate.close();self.gate=FLAY217(os.path.join(self.tmp.name,'db'));self.assertEqual(self.check(),'REPLAY')
    def test_invalid_plan_signature(self):self.parts[0]['signature']='00';self.assertEqual(self.check(),'SIGNATURE_INVALID')
    def test_invalid_commit_signature(self):self.parts[1]['signature']='00';self.assertEqual(self.check(),'SIGNATURE_INVALID')
    def test_invalid_reveal_signature(self):self.parts[2]['signature']='00';self.assertEqual(self.check(),'SIGNATURE_INVALID')
    def test_invalid_response_signature(self):self.parts[3]['signature']='00';self.assertEqual(self.check(),'SIGNATURE_INVALID')
    def test_invalid_witness_signature(self):self.parts[4][0]['signature']='00';self.assertEqual(self.check(),'SIGNATURE_INVALID')
    def test_challenge_mismatch_commit(self):self.change(1,challenge='wrong');self.assertEqual(self.check(),'CHALLENGE_MISMATCH')
    def test_challenge_mismatch_reveal(self):self.change(2,challenge='wrong');self.assertEqual(self.check(),'CHALLENGE_MISMATCH')
    def test_challenge_mismatch_response(self):self.change(3,challenge='wrong');self.assertEqual(self.check(),'CHALLENGE_MISMATCH')
    def test_bad_task_commit(self):self.change(1,task_hash='wrong');self.assertEqual(self.check(),'PLAN_COMMITMENT_MISMATCH')
    def test_bad_plan_hash(self):self.change(1,plan_hash='wrong');self.assertEqual(self.check(),'PLAN_COMMITMENT_MISMATCH')
    def test_commit_before_freeze(self):self.change(1,commit_time=99);self.assertEqual(self.check(),'INVALID_CHRONOLOGY')
    def test_release_before_commit(self):self.change(2,release_time=105);self.assertEqual(self.check(),'INVALID_CHRONOLOGY')
    def test_capture_before_release(self):self.change(3,capture_time=120);self.assertEqual(self.check(),'INVALID_CHRONOLOGY')
    def test_capture_after_deadline(self):self.change(3,capture_time=205);self.assertEqual(self.check(),'INVALID_CHRONOLOGY')
    def test_equal_times(self):self.change(2,release_time=110);self.assertEqual(self.check(),'INVALID_CHRONOLOGY')
    def test_wrong_seed(self):self.change(2,seed='ef'*32);self.assertEqual(self.check(),'SEED_COMMITMENT_MISMATCH')
    def test_short_seed(self):self.change(2,seed='aa');self.assertEqual(self.check(),'INVALID_SEED')
    def test_invalid_seed_hex(self):self.change(2,seed='zz'*32);self.assertEqual(self.check(),'MALFORMED_EVIDENCE')
    def test_reveal_wrong_commit(self):self.change(2,commit_hash='00'*32);self.assertEqual(self.check(),'REVEAL_COMMITMENT_MISMATCH')
    def test_reveal_wrong_pattern(self):self.change(2,pattern='00'*16);self.assertEqual(self.check(),'PATTERN_MISMATCH')
    def test_response_wrong_pattern(self):self.change(3,pattern='00'*16);self.assertEqual(self.check(),'RESPONSE_PATTERN_MISMATCH')
    def test_response_wrong_task(self):self.change(3,task_hash='wrong');self.assertEqual(self.check(),'RESPONSE_BINDING_MISMATCH')
    def test_response_wrong_release(self):self.change(3,release_hash='wrong');self.assertEqual(self.check(),'RESPONSE_BINDING_MISMATCH')
    def test_witness_wrong_response(self):self.parts[4][0]=signed(self.parts[6]['w0'],dict(self.parts[4][0]['body'],response_hash='wrong'));self.assertEqual(self.check(),'WITNESS_RESPONSE_MISMATCH')
    def test_witness_wrong_capture(self):self.parts[4][1]=signed(self.parts[6]['w1'],dict(self.parts[4][1]['body'],capture_hash='wrong'));self.assertEqual(self.check(),'WITNESS_RESPONSE_MISMATCH')
    def test_witness_early(self):self.parts[4][0]=signed(self.parts[6]['w0'],dict(self.parts[4][0]['body'],observed_time=139));self.assertEqual(self.check(),'WITNESS_CHRONOLOGY_INVALID')
    def test_witness_late(self):self.parts[4][0]=signed(self.parts[6]['w0'],dict(self.parts[4][0]['body'],observed_time=201));self.assertEqual(self.check(),'WITNESS_CHRONOLOGY_INVALID')
    def test_shared_root(self):self.parts[4][1]=signed(self.parts[6]['w1'],dict(self.parts[4][1]['body'],root='root-0'));self.assertEqual(self.check(),'SHARED_OBSERVATION_ROOT')
    def test_shared_sensor(self):self.parts[4][1]=signed(self.parts[6]['w1'],dict(self.parts[4][1]['body'],sensor='sensor-0'));self.assertEqual(self.check(),'SHARED_OBSERVATION_ROOT')
    def test_early_disclosure_report(self):self.change(2,early_disclosure=True);self.assertEqual(self.check(),'PREMATURE_DISCLOSURE_REPORTED')
    def test_corrupt_log(self):self.check();self.gate.connection.execute("UPDATE audit SET body='fake'");self.gate.connection.commit();self.assertEqual(self.check(),'CORRUPT_LOG')
    def test_fresh_fixture_unique_pattern(self):self.assertNotEqual(fixture(bytes.fromhex('ab'*32))[2]['body']['pattern'],fixture(bytes.fromhex('bc'*32))[2]['body']['pattern'])
    def test_deterministic_fixture(self):self.assertEqual(fixture(bytes.fromhex('ab'*32))[2]['body']['pattern'],fixture(bytes.fromhex('ab'*32))[2]['body']['pattern'])
    def test_audit(self):self.check();self.assertTrue(self.gate.audit_ok())
    def test_demo(self):self.assertEqual(run_demo()['scenarios']['baseline']['status'],'CHALLENGE_RESPONSE_CONSISTENT_FIXTURE')

if __name__=='__main__': unittest.main()