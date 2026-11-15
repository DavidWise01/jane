import copy,os,sqlite3,tempfile,unittest
from acquisition import FLAY214,Ledger,Policy,canonical,fixture,sha

class TestJANE214(unittest.TestCase):
    def setUp(self):self.p,self.pubs,self.priv=fixture();self.l=Ledger();self.v=FLAY214(self.pubs,self.l)
    def tearDown(self):self.l.close()
    def resign(self,i):
        p=self.p['observations'][i];p['signature']=self.priv[p['body']['id']].sign(canonical(p['body'])).hex()
    def expect(self, verdict):self.assertEqual(self.v.inspect(self.p)['verdict'],verdict)
    def test_fresh(self):self.expect('FRESH_ACQUISITION_FIXTURE')
    def test_replay(self):self.v.inspect(self.p);self.expect('REPLAY_CHALLENGE')
    def test_fresh_tamper(self):self.p['observations'][0]['body']['frame']=99;self.expect('SIGNATURE_INVALID')
    def test_bad_challenge_signature(self):self.p['challenge']['signature']='00';self.expect('SIGNATURE_INVALID')
    def test_bad_observation_signature(self):self.p['observations'][0]['signature']='00';self.expect('SIGNATURE_INVALID')
    def test_shared_root(self):self.p['observations'][1]['body']['root']='root-scope-a';self.resign(1);self.expect('SHARED_ANCESTRY')
    def test_shared_sensor(self):self.p['observations'][1]['body']['sensor']='sensor-scope-a';self.resign(1);self.expect('SHARED_SENSOR')
    def test_capture_before_challenge(self):self.p['observations'][0]['body']['start']=99;self.resign(0);self.expect('INVALID_CAPTURE_CHRONOLOGY')
    def test_capture_after_expiration(self):self.p['observations'][0]['body']['end']=161;self.resign(0);self.expect('INVALID_CAPTURE_CHRONOLOGY')
    def test_capture_end_before_start(self):self.p['observations'][0]['body']['end']=109;self.resign(0);self.expect('INVALID_CAPTURE_CHRONOLOGY')
    def test_capture_too_slow(self):self.p['observations'][0]['body']['end']=150;self.resign(0);self.expect('INVALID_CAPTURE_CHRONOLOGY')
    def test_wrong_nonce(self):self.p['observations'][0]['body']['nonce']='b'*32;self.resign(0);self.expect('CHALLENGE_MISMATCH')
    def test_wrong_task(self):self.p['observations'][0]['body']['task']='b'*64;self.resign(0);self.expect('CHALLENGE_MISMATCH')
    def test_payload_disagreement(self):self.p['observations'][0]['body']['payload_hash']='b'*64;self.resign(0);self.expect('EFFECT_DISAGREEMENT')
    def test_empty_provenance(self):self.p['observations'][0]['body']['root']='';self.resign(0);self.expect('MISSING_PROVENANCE')
    def test_missing_boot(self):self.p['observations'][0]['body']['sensor_boot']='';self.resign(0);self.expect('MISSING_BOOT_PROVENANCE')
    def test_invalid_frame(self):self.p['observations'][0]['body']['frame']=-1;self.resign(0);self.expect('INVALID_FRAME')
    def test_duplicate_capture(self):self.p['observations'][1]['body']['capture_id']=self.p['observations'][0]['body']['capture_id'];self.resign(1);self.expect('REPLAY_CAPTURE')
    def test_missing_observations(self):self.p['observations']=[];self.expect('MISSING_OBSERVATIONS')
    def test_nonce_short(self):self.p['challenge']['body']['nonce']='abc';self.expect('INVALID_NONCE')
    def test_duplicate_signer(self):self.p['observations'].append(copy.deepcopy(self.p['observations'][0]));self.expect('DUPLICATE_SIGNER')
    def test_unrecognized_signer(self):self.p['observations'][0]['body']['id']='alien';self.expect('SIGNATURE_INVALID')
    def test_invalid_task(self):self.p['challenge']['body']['task']='tiny';self.p['challenge']['signature']=self.priv['scheduler'].sign(canonical(self.p['challenge']['body'])).hex();self.expect('INVALID_TASK')
    def test_invalid_challenge_clock(self):self.p['challenge']['body']['issued']=200;self.p['challenge']['signature']=self.priv['scheduler'].sign(canonical(self.p['challenge']['body'])).hex();self.expect('INVALID_CHRONOLOGY')
    def test_replay_after_restart(self):
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,'ledger.sqlite');a=Ledger(path);self.assertEqual(FLAY214(self.pubs,a).inspect(self.p)['verdict'],'FRESH_ACQUISITION_FIXTURE');a.close();b=Ledger(path);self.assertEqual(FLAY214(self.pubs,b).inspect(self.p)['verdict'],'REPLAY_CHALLENGE');b.close()
    def test_capture_reuse_new_challenge(self):
        self.v.inspect(self.p)
        self.p['challenge']['body']['nonce']='c'*32;self.p['challenge']['signature']=self.priv['scheduler'].sign(canonical(self.p['challenge']['body'])).hex()
        for i in range(2):self.p['observations'][i]['body']['nonce']='c'*32;self.resign(i)
        self.expect('REPLAY_CAPTURE')
    def test_audit_corruption(self):self.v.inspect(self.p);self.l.db.execute("UPDATE audit SET event='{}' WHERE seq=1");self.l.db.commit();self.expect('CORRUPT_AUDIT')
    def test_custom_policy(self):self.assertEqual(FLAY214(self.pubs,self.l,Policy(min_roots=3)).inspect(self.p)['verdict'],'SHARED_ANCESTRY')
    def test_missing_packet(self):self.assertEqual(self.v.inspect({})['verdict'],'MALFORMED_EVIDENCE')
    def test_no_ledger_mutation_on_reject(self):self.p['observations'][0]['signature']='00';self.expect('SIGNATURE_INVALID');self.assertEqual(self.l.db.execute('SELECT count(*) FROM used').fetchone()[0],0)

if __name__=='__main__':unittest.main()