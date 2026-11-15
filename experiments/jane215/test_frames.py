import unittest, tempfile, os, copy
from frames import *
class TestFrames(unittest.TestCase):
    def setUp(self):
        self.ledger=Ledger();self.packet,self.private,self.public=fixture();self.flay=FLAY215(self.public,self.ledger)
    def tearDown(self):self.ledger.close()
    def resign(self,idx):
        p=self.packet['observations'][idx];who=p['body']['id'];self.packet['observations'][idx]=signed(p['body'],self.private[who])
    def test_first(self):self.assertEqual(self.flay.inspect(self.packet)['verdict'],'NOVEL_CONTENT_FIXTURE')
    def test_replay(self):self.flay.inspect(self.packet);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'REPLAY_CHALLENGE')
    def test_reencoding(self):
        self.flay.inspect(self.packet);p,_,_=fixture(2,encoding='jpeg');self.assertEqual(self.flay.inspect(p)['verdict'],'REPEATED_CONTENT_SUSPECTED')
    def test_changed_pixels(self):
        self.flay.inspect(self.packet);p,_,_=fixture(2,pixels=[12,24,38,77,99,120,201,144,39,44,62,80]);self.assertEqual(self.flay.inspect(p)['verdict'],'NOVEL_CONTENT_FIXTURE')
    def test_repeat_still_committed(self):
        self.flay.inspect(self.packet);p,_,_=fixture(2);self.flay.inspect(p);self.assertEqual(self.flay.inspect(p)['verdict'],'REPLAY_CHALLENGE')
    def test_repeated_sequence(self):
        self.flay.inspect(self.packet);p,_,_=fixture(2,seq=1);self.assertEqual(self.flay.inspect(p)['verdict'],'REPLAY_SENSOR_SEQUENCE')
    def test_bad_signature(self):
        self.packet['observations'][0]['signature']='00';self.assertEqual(self.flay.inspect(self.packet)['verdict'],'SIGNATURE_INVALID')
    def test_bad_issuer_signature(self):
        self.packet['challenge']['signature']='00';self.assertEqual(self.flay.inspect(self.packet)['verdict'],'SIGNATURE_INVALID')
    def test_challenge_mismatch(self):
        self.packet['observations'][0]['body']['nonce']='other';self.resign(0);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'CHALLENGE_MISMATCH')
    def test_shared_sensor(self):
        self.packet['observations'][1]['body']['sensor']='sensor-a';self.resign(1);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'SHARED_SENSOR')
    def test_shared_root(self):
        self.packet['observations'][1]['body']['root']='root-a';self.resign(1);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'SHARED_ANCESTRY')
    def test_late_capture(self):
        self.packet['observations'][0]['body']['tick']=999;self.resign(0);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'INVALID_CAPTURE_CHRONOLOGY')
    def test_bad_content_hash(self):
        self.packet['observations'][0]['body']['pixels'][0]=19;self.resign(0);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'CONTENT_FINGERPRINT_MISMATCH')
    def test_disagreement(self):
        b=self.packet['observations'][0]['body'];b['pixels'][0]=19;b['fingerprint']=pixels_hash(2,2,b['pixels']);self.resign(0);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'CONTENT_DISAGREEMENT')
    def test_short_pixels(self):
        self.packet['observations'][0]['body']['pixels']=[0];self.resign(0);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'MALFORMED_EVIDENCE')
    def test_wrong_channel(self):
        self.packet['observations'][0]['body']['pixels'][0]=-1;self.resign(0);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'MALFORMED_EVIDENCE')
    def test_tampered_chain(self):
        self.flay.inspect(self.packet);self.ledger.db.execute('UPDATE audit SET head=?',('x',));self.ledger.db.commit();self.assertEqual(self.flay.inspect(fixture(2)[0])['verdict'],'CORRUPT_AUDIT')
    def test_restart(self):
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,'s.db');a=Ledger(path);FLAY215(self.public,a).inspect(self.packet);a.close();b=Ledger(path)
            try:self.assertEqual(FLAY215(self.public,b).inspect(self.packet)['verdict'],'REPLAY_CHALLENGE')
            finally:b.close()
    def test_ledger_no_physical_claim(self):self.assertFalse(self.flay.inspect(self.packet)['physical_freshness_proven'])
    def test_fingerprint_encoding_independent(self):
        p,_,_=fixture(1,encoding='raw');self.assertEqual(p['observations'][0]['body']['fingerprint'],self.packet['observations'][0]['body']['fingerprint'])
    def test_pixel_hash_dimensions(self):
        self.assertNotEqual(pixels_hash(2,2,[1]*12),pixels_hash(1,4,[1]*12))
    def test_zero_size(self):
        with self.assertRaises(ValueError):pixels_hash(0,2,[])
    def test_boolean_pixel(self):
        with self.assertRaises(ValueError):pixels_hash(1,1,[True,0,0])
    def test_duplicate_observer(self):
        self.packet['observations'].append(self.packet['observations'][0]);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'SHARED_ANCESTRY')
    def test_missing_observers(self):self.packet['observations']=[];self.assertEqual(self.flay.inspect(self.packet)['verdict'],'INSUFFICIENT_OBSERVATIONS')
    def test_nonce_short(self):
        self.packet['challenge']['body']['nonce']='x';self.packet['challenge']=signed(self.packet['challenge']['body'],self.private['issuer']);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'INVALID_NONCE')
    def test_invalid_sequence(self):
        self.packet['observations'][0]['body']['seq']=0;self.resign(0);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'INVALID_SENSOR_SEQUENCE')
    def test_wrong_timestamp_type(self):
        self.packet['observations'][0]['body']['tick']=True;self.resign(0);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'INVALID_CAPTURE_CHRONOLOGY')
    def test_bad_challenge_timestamp(self):
        self.packet['challenge']['body']['expires']=0;self.packet['challenge']=signed(self.packet['challenge']['body'],self.private['issuer']);self.assertEqual(self.flay.inspect(self.packet)['verdict'],'INVALID_CHRONOLOGY')
    def test_no_mutation_on_rejection(self):
        self.packet['observations'][0]['signature']='00';self.flay.inspect(self.packet);self.assertEqual(self.ledger.db.execute('SELECT COUNT(*) FROM challenge').fetchone()[0],0)
if __name__=='__main__':unittest.main()