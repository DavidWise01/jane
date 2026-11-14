import unittest, tempfile, os, copy
from fresh import *
class FreshTest(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.path=os.path.join(self.t.name,'audit.db')
        self.keys=fixture_keys();self.pub={n:key.public_key() for n,key in self.keys.items()}
        self.db=FLAY(self.path,self.pub,{'observerA':'rA','observerB':'rB'})
        self.q=challenge(self.keys['issuer'],b'job',1,100,200,'a'*32)
        self.run=execution(self.keys['executor'],self.q,b'out',120)
        self.obs=[effect(self.keys[n],n,self.q,b'out',130,source) for n,source in [('observerA','sA'),('observerB','sB')]]
    def tearDown(self):self.db.close();self.t.cleanup()
    def check(self,verdict,request=None,run=None,obs=None,now=140,data=b'job',quorum=2):
        return self.assertEqual(self.db.review(data,request if request is not None else self.q,run if run is not None else self.run,obs if obs is not None else self.obs,now,quorum),verdict)
    def test_success(self):self.check('FRESH_EFFECT_FIXTURE_CORROBORATED')
    def test_replay(self):self.check('FRESH_EFFECT_FIXTURE_CORROBORATED');self.check('REPLAY')
    def test_restart_replay(self):
        self.check('FRESH_EFFECT_FIXTURE_CORROBORATED');self.db.close();self.db=FLAY(self.path,self.pub,{'observerA':'rA','observerB':'rB'});self.check('REPLAY')
    def test_forged_challenge(self):
        q=copy.deepcopy(self.q);q['body']['issued_ms']=0;self.check('BAD_CHALLENGE_SIGNATURE',request=q)
    def test_forged_execution(self):
        r=copy.deepcopy(self.run);r['body']['observed_ms']=150;self.check('BAD_EXECUTION_SIGNATURE',run=r)
    def test_forged_effect(self):
        o=copy.deepcopy(self.obs);o[0]['body']['source_id']='fake';self.check('BAD_EFFECT_SIGNATURE',obs=o)
    def test_expired(self):self.check('CHALLENGE_EXPIRED_OR_FUTURE',now=201)
    def test_future(self):self.check('CHALLENGE_EXPIRED_OR_FUTURE',now=99)
    def test_input(self):self.check('INPUT_MISMATCH',data=b'bad')
    def test_empty_effects(self):self.check('SUCCESS_UNCORROBORATED',obs=[])
    def test_staged_old_nonce(self):
        old=challenge(self.keys['issuer'],b'job',2,100,200,'b'*32)
        o=copy.deepcopy(self.obs);o[0]=effect(self.keys['observerA'],'observerA',old,b'out',130,'sA');self.check('STAGED_OR_MISMATCHED_EFFECT',obs=o)
    def test_wrong_output(self):
        o=copy.deepcopy(self.obs);o[0]=effect(self.keys['observerA'],'observerA',self.q,b'other',130,'sA');self.check('STAGED_OR_MISMATCHED_EFFECT',obs=o)
    def test_execution_nonce(self):
        old=challenge(self.keys['issuer'],b'job',2,100,200,'b'*32)
        r=execution(self.keys['executor'],old,b'out',120);self.check('EXECUTION_NOT_BOUND',run=r)
    def test_execution_predates_request(self):self.check('EXECUTION_TIME_UNSUPPORTED',run=execution(self.keys['executor'],self.q,b'out',99))
    def test_effect_predates_execution(self):
        o=copy.deepcopy(self.obs);o[0]=effect(self.keys['observerA'],'observerA',self.q,b'out',119,'sA');self.check('EFFECT_ORDER_UNSUPPORTED',obs=o)
    def test_effect_after_deadline(self):
        o=copy.deepcopy(self.obs);o[0]=effect(self.keys['observerA'],'observerA',self.q,b'out',201,'sA');self.check('EFFECT_ORDER_UNSUPPORTED',obs=o,now=200)
    def test_failed_execution(self):self.check('FAILED_ATTEMPT_PRESERVED',run=execution(self.keys['executor'],self.q,b'',120,'FAILED'))
    def test_duplicate_observer(self):self.check('DUPLICATE_OBSERVER',obs=[self.obs[0],self.obs[0]])
    def test_same_root(self):self.db.roots['observerB']='rA';self.check('SHARED_OR_INSUFFICIENT_ANCESTRY')
    def test_same_instrument(self):
        o=copy.deepcopy(self.obs);o[1]=effect(self.keys['observerB'],'observerB',self.q,b'out',130,'sA');self.check('SHARED_OR_INSUFFICIENT_ANCESTRY',obs=o)
    def test_unknown_source(self):
        o=copy.deepcopy(self.obs);o[0]=effect(self.keys['observerA'],'observerA',self.q,b'out',130,'');self.check('MISSING_ACQUISITION_SOURCE',obs=o)
    def test_insufficient(self):self.check('SHARED_OR_INSUFFICIENT_ANCESTRY',obs=[self.obs[0]])
    def test_larger_quorum(self):self.check('SHARED_OR_INSUFFICIENT_ANCESTRY',quorum=3)
    def test_audit(self):self.check('FRESH_EFFECT_FIXTURE_CORROBORATED');self.assertTrue(self.db.audit_ok())
    def test_tamper_audit(self):
        self.check('FRESH_EFFECT_FIXTURE_CORROBORATED');self.db.db.execute("update audit set payload='{}' where id=1");self.db.db.commit();self.assertFalse(self.db.audit_ok())
    def test_nonce_consumed_on_failure(self):self.check('SUCCESS_UNCORROBORATED',obs=[]);self.check('REPLAY')
    def test_nonce_validity(self):
        with self.assertRaises(ValueError):challenge(self.keys['issuer'],b'x',1,0,1,'a')
    def test_deterministic_demo(self):self.assertEqual(demo(),demo())
    def test_demo(self):self.assertEqual(demo()['status'],'FRESH_EFFECT_FIXTURE_CORROBORATED')
    def test_no_activation(self):self.check('FRESH_EFFECT_FIXTURE_CORROBORATED');self.assertEqual(self.db.active,'frozen_parent')
    def test_two_distinct_sources(self):self.assertNotEqual(self.obs[0]['body']['source_id'],self.obs[1]['body']['source_id'])
    def test_bad_executor_identity(self):
        r=packet(self.keys['observerA'],'executor',self.run['body']);self.check('BAD_EXECUTION_SIGNATURE',run=r)
    def test_bad_time_type(self):self.check('CHALLENGE_EXPIRED_OR_FUTURE',now=140.0)
if __name__=='__main__':unittest.main(verbosity=2)