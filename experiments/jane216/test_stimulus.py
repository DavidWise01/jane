import copy,os,tempfile,unittest
from stimulus import *
class TestStimulus(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.a=Audit(os.path.join(self.tmp.name,'a.db'));self.f=FLAY216(self.a)
 def tearDown(self):self.a.close();self.tmp.cleanup()
 def check(self,mode,expected):self.assertEqual(self.f.evaluate(make_fixture(mode)),expected)
 def test_valid(self):self.check('valid','CHALLENGE_RESPONSE_CONSISTENT_FIXTURE')
 def test_old(self):self.check('old_frame','STIMULUS_RESPONSE_MISMATCH')
 def test_early(self):self.check('early','CAPTURE_OUTSIDE_WINDOW')
 def test_late(self):self.check('late','CAPTURE_OUTSIDE_WINDOW')
 def test_nonce(self):self.check('wrong_nonce','CHALLENGE_BINDING_MISMATCH')
 def test_shared_root(self):self.check('shared_root','SHARED_OBSERVATION_ANCESTRY')
 def test_shared_operator(self):self.check('shared_operator','SHARED_OBSERVATION_ANCESTRY')
 def test_sensor_witness(self):self.check('sensor_as_witness','SHARED_OBSERVATION_ANCESTRY')
 def test_mismatch(self):self.check('mismatch','WITNESS_CONTENT_MISMATCH')
 def test_witness_early(self):self.check('witness_early','WITNESS_CHRONOLOGY_INVALID')
 def test_tamper(self):self.check('tamper','SIGNATURE_INVALID')
 def test_tamper_challenge(self):self.check('tamper_challenge','SIGNATURE_INVALID')
 def test_replay(self):
  self.check('valid','CHALLENGE_RESPONSE_CONSISTENT_FIXTURE');self.check('valid','REPLAY_CHALLENGE')
 def test_replay_after_restart(self):
  self.check('valid','CHALLENGE_RESPONSE_CONSISTENT_FIXTURE');self.a.close();self.a=Audit(os.path.join(self.tmp.name,'a.db'));self.f=FLAY216(self.a);self.check('valid','REPLAY_CHALLENGE')
 def test_capture_reuse(self):
  self.check('valid','CHALLENGE_RESPONSE_CONSISTENT_FIXTURE');e=make_fixture(nonce='new-challenge');self.assertEqual(self.f.evaluate(e),'REPLAY_CAPTURE')
 def test_new_capture_pass(self):
  self.check('valid','CHALLENGE_RESPONSE_CONSISTENT_FIXTURE');e=make_fixture(nonce='new-challenge');e['capture']['body']['capture_id']='new-capture';e['capture']=signed('sensor',e['capture']['body']);body=e['capture']['body'];e['witnesses']=[signed('witness-'+x['body']['name'],dict(x['body'],capture_id='new-capture',response_digest=digest(body))) for x in e['witnesses']];self.assertEqual(self.f.evaluate(e),'CHALLENGE_RESPONSE_CONSISTENT_FIXTURE')
 def test_wrong_observer_name(self):
  e=make_fixture();e['witnesses'][0]=signed('witness-A',dict(e['witnesses'][0]['body'],name='X'));self.assertEqual(self.f.evaluate(e),'INVALID_WITNESS_SET')
 def test_wrong_capture_reference(self):
  e=make_fixture();e['witnesses'][0]=signed('witness-A',dict(e['witnesses'][0]['body'],capture_id='unknown'));self.assertEqual(self.f.evaluate(e),'WITNESS_CONTENT_MISMATCH')
 def test_wrong_sensor_reference(self):
  e=make_fixture();e['witnesses'][0]=signed('witness-A',dict(e['witnesses'][0]['body'],sensor_root='wrong'));self.assertEqual(self.f.evaluate(e),'WITNESS_CONTENT_MISMATCH')
 def test_invalid_timing(self):
  e=make_fixture();e['challenge']=signed('controller',dict(e['challenge']['body'],deadline=110));self.assertEqual(self.f.evaluate(e),'INVALID_STIMULUS_CHRONOLOGY')
 def test_witness_late(self):
  e=make_fixture();e['witnesses'][0]=signed('witness-A',dict(e['witnesses'][0]['body'],observed_at=200));self.assertEqual(self.f.evaluate(e),'WITNESS_CHRONOLOGY_INVALID')
 def test_bad_sensor_signer(self):
  e=make_fixture();e['capture']=signed('controller',e['capture']['body']);self.assertEqual(self.f.evaluate(e),'SIGNATURE_INVALID')
 def test_one_witness(self):
  e=make_fixture();e['witnesses'].pop();self.assertEqual(self.f.evaluate(e),'SIGNATURE_INVALID')
 def test_blank_witness(self):
  e=make_fixture();e['witnesses'][0]['signature']='invalid';self.assertEqual(self.f.evaluate(e),'SIGNATURE_INVALID')
 def test_bad_frame_hash_signature(self):
  e=make_fixture();e['capture']['body']['frame_digest']='0'*64;self.assertEqual(self.f.evaluate(e),'SIGNATURE_INVALID')
 def test_same_challenge_different_capture(self):
  self.check('valid','CHALLENGE_RESPONSE_CONSISTENT_FIXTURE');e=make_fixture();e['capture']['body']['capture_id']='different';e['capture']=signed('sensor',e['capture']['body']);self.assertEqual(self.f.evaluate(e),'REPLAY_CHALLENGE')
 def test_invalid_evidence(self):self.assertEqual(self.f.evaluate({}),'INVALID_EVIDENCE')
 def test_hash_deterministic(self):self.assertEqual(digest({'a':1,'b':2}),digest({'b':2,'a':1}))
 def test_signed_verify(self):self.assertTrue(verify(pub('controller'),signed('controller',{'a':1})))
 def test_wrong_key(self):self.assertFalse(verify(pub('sensor'),signed('controller',{'a':1})))
 def test_audit_chain(self):self.check('valid','CHALLENGE_RESPONSE_CONSISTENT_FIXTURE');self.assertTrue(self.a.chain_valid())
 def test_audit_tamper(self):
  self.check('valid','CHALLENGE_RESPONSE_CONSISTENT_FIXTURE');self.a.db.execute("UPDATE events SET payload='corrupt' WHERE seq=1");self.a.db.commit();self.assertEqual(self.f.evaluate(make_fixture(nonce='new')),'CORRUPT_AUDIT')
 def test_no_physical_proof(self):self.assertFalse(demonstration()['physical_capture_proven'])
 def test_freeze(self):self.assertEqual(demonstration()['parent'],'frozen')
if __name__=='__main__':unittest.main()