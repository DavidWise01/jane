import unittest,tempfile,os
from witnessed_reveal import *
class Checks(unittest.TestCase):
    def setUp(self):
        self.trust,self.freeze,self.manifest,self.witnesses,self.reveal=fixture()
        self.a=Auditor(':memory:',self.trust)
    def tearDown(self):self.a.close()
    def check(self):return self.a.evaluate(self.freeze,self.manifest,self.witnesses,self.reveal,150)['status']
    def test_valid(self):self.assertEqual(self.check(),'WITNESSED_REVEAL_FIXTURE')
    def test_replay(self):self.check();self.assertEqual(self.check(),'REPLAY')
    def test_log(self):self.check();self.assertTrue(self.a.audit_log())
    def test_bad_task_signature(self):self.freeze['body']['tick']=99;self.assertEqual(self.check(),'BAD_TASK_SIGNATURE')
    def test_bad_commit_signature(self):self.manifest['body']['tick']=109;self.assertEqual(self.check(),'BAD_COMMIT_SIGNATURE')
    def test_bad_reveal_signature(self):self.reveal['body']['tick']=141;self.assertEqual(self.check(),'BAD_REVEAL_SIGNATURE')
    def test_bad_witness_signature(self):self.witnesses[0]['body']['tick']=122;self.assertEqual(self.check(),'BAD_WITNESS_SIGNATURE')
    def test_insufficient(self):self.witnesses=self.witnesses[:1];self.assertEqual(self.check(),'INSUFFICIENT_DECLARED_CUSTODY')
    def test_duplicate(self):self.witnesses=[self.witnesses[0],self.witnesses[0]];self.assertEqual(self.check(),'DUPLICATE_WITNESS')
    def test_shared_origin(self):
        self.trust,self.freeze,self.manifest,self.witnesses,self.reveal=fixture(shared_origin=True)
        self.a.close();self.a=Auditor(':memory:',self.trust)
        self.assertEqual(self.check(),'INSUFFICIENT_DECLARED_CUSTODY')
    def test_witness_before_commit(self):
        b=dict(self.witnesses[0]['body']);b['tick']=109
        self.witnesses[0]=signed(deterministic_key('A'),b)
        self.assertEqual(self.check(),'WITNESS_BEFORE_COMMIT')
    def test_reveal_before_witness(self):
        b=dict(self.reveal['body']);b['tick']=121
        self.reveal=signed(deterministic_key('reveal'),b)
        self.assertEqual(self.check(),'REVEAL_BEFORE_WITNESS')
    def test_early_disclosure(self):
        self.trust,self.freeze,self.manifest,self.witnesses,self.reveal=fixture(disclose_early=True)
        self.a.close();self.a=Auditor(':memory:',self.trust)
        self.assertEqual(self.check(),'PREMATURE_DISCLOSURE_REPORTED')
    def test_bad_seed(self):
        b=dict(self.reveal['body']);b['seed']='0'*64;self.reveal=signed(deterministic_key('reveal'),b)
        self.assertEqual(self.check(),'COMMITMENT_MISMATCH')
    def test_malformed_seed(self):
        b=dict(self.reveal['body']);b['seed']='oops';self.reveal=signed(deterministic_key('reveal'),b)
        self.assertEqual(self.check(),'BAD_SEED')
    def test_future(self):
        b=dict(self.reveal['body']);b['tick']=160;self.reveal=signed(deterministic_key('reveal'),b)
        self.assertEqual(self.check(),'FUTURE_REVEAL')
    def test_tamper_log(self):
        self.check();self.a.db.execute("UPDATE log SET event='{}' WHERE seq=0");self.assertFalse(self.a.audit_log())
    def test_persist_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=os.path.join(tmp,'e.db');a=Auditor(path,self.trust)
            self.assertEqual(a.evaluate(self.freeze,self.manifest,self.witnesses,self.reveal,150)['status'],'WITNESSED_REVEAL_FIXTURE');a.close()
            b=Auditor(path,self.trust)
            self.assertEqual(b.evaluate(self.freeze,self.manifest,self.witnesses,self.reveal,151)['status'],'REPLAY');b.close()
    def test_two_witnesses(self):self.witnesses=self.witnesses[:2];self.assertEqual(self.check(),'WITNESSED_REVEAL_FIXTURE')
    def test_wrong_task(self):
        b=dict(self.reveal['body']);b['task_hash']='e'*64;self.reveal=signed(deterministic_key('reveal'),b)
        self.assertEqual(self.check(),'REVEAL_TASK_MISMATCH')
    def test_wrong_commit(self):
        b=dict(self.manifest['body']);b['seed_commitment']='f'*64;self.manifest=signed(deterministic_key('commit'),b)
        self.assertEqual(self.check(),'WITNESS_COMMIT_CONFLICT')
    def test_missing_disclosure(self):
        b=dict(self.reveal['body']);b.pop('first_disclosure_tick');self.reveal=signed(deterministic_key('reveal'),b)
        self.assertEqual(self.check(),'MISSING_DISCLOSURE_HISTORY')
    def test_signature_validity_not_secrecy(self):self.assertEqual(demo()['custody_independence'],'UNVERIFIED_FIXTURE')
    def test_sha_deterministic(self):self.assertEqual(sha({'a':1,'b':2}),sha({'b':2,'a':1}))
    def test_commit_domain(self):self.assertNotEqual(sha({'seed':'0'*64}),commitment('a'*64,'0'*64))
if __name__=='__main__':unittest.main(verbosity=2)
