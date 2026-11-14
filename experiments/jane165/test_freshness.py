import unittest, tempfile, os
from freshness import *

class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.keys,self.trusted,self.head=fixture();self.now=1700000300
        self.policy=Policy(max_age=300,future_skew=30,quorum=3)
    def receipt(self,i=0,age=10,sequence=6,head=None,nonce='nonce'):
        return make_receipt(self.keys[i],f'fixture-{i}',f'admin-{i}',sequence,head or self.head,self.now-age,nonce+str(i))
    def engine(self,**kw):return FLAY165(self.trusted,self.policy,**kw)
    def group(self,age=10):return [self.receipt(i,age=age) for i in range(3)]
    def test_demo_fresh(self):self.assertEqual(demo()['fresh']['decision'],'FRESH_FIXTURE_QUORUM_NO_COMPLETENESS_PROOF')
    def test_demo_stale(self):self.assertEqual(demo()['stale']['decision'],'AUTHENTIC_HISTORIC_ONLY')
    def test_exact_age(self):self.assertEqual(self.engine().verify_one(self.receipt(age=300),self.now)[0],'FRESH_HISTORY')
    def test_over_age(self):self.assertEqual(self.engine().verify_one(self.receipt(age=301),self.now)[0],'STALE_HISTORY')
    def test_future_boundary(self):self.assertEqual(self.engine().verify_one(self.receipt(age=-30),self.now)[0],'FRESH_HISTORY')
    def test_future_excess(self):self.assertEqual(self.engine().verify_one(self.receipt(age=-31),self.now)[0],'FUTURE_CLOCK')
    def test_invalid_now(self):
        with self.assertRaises(ValueError):self.engine().verify_one(self.receipt(),-1)
    def test_bool_clock_invalid(self):
        with self.assertRaises(ValueError):self.engine().verify_one(self.receipt(),True)
    def test_tamper_age(self):
        r=self.receipt();r['payload']['observed_at']-=1000
        self.assertEqual(self.engine().verify_one(r,self.now)[0],'BAD_SIGNATURE')
    def test_tamper_sequence(self):
        r=self.receipt();r['payload']['sequence']+=1
        self.assertEqual(self.engine().verify_one(r,self.now)[0],'BAD_SIGNATURE')
    def test_tamper_head(self):
        r=self.receipt();r['payload']['head']='cd'*32
        self.assertEqual(self.engine().verify_one(r,self.now)[0],'BAD_SIGNATURE')
    def test_bad_signature(self):
        r=self.receipt();r['signature']='00'*64
        self.assertEqual(self.engine().verify_one(r,self.now)[0],'BAD_SIGNATURE')
    def test_unknown_root(self):
        r=self.receipt();r['payload']['root']='stranger'
        self.assertEqual(self.engine().verify_one(r,self.now)[0],'UNKNOWN_ROOT')
    def test_admin_mismatch(self):
        r=self.receipt();r['payload']['administrator']='wrong'
        self.assertEqual(self.engine().verify_one(r,self.now)[0],'ADMIN_MISMATCH')
    def test_wrong_protocol(self):
        r=self.receipt();r['payload']['protocol']='JANE999'
        self.assertEqual(self.engine().verify_one(r,self.now)[0],'BAD_FORMAT')
    def test_missing_field(self):
        r=self.receipt();del r['payload']['nonce']
        self.assertEqual(self.engine().verify_one(r,self.now)[0],'BAD_FORMAT')
    def test_extra_field(self):
        r=self.receipt();r['payload']['secret']='oops'
        self.assertEqual(self.engine().verify_one(r,self.now)[0],'BAD_FORMAT')
    def test_invalid_head(self):
        r=self.receipt();r['payload']['head']='invalid'
        self.assertEqual(self.engine().verify_one(r,self.now)[0],'BAD_FORMAT')
    def test_negative_seq(self):
        r=self.receipt();r['payload']['sequence']=-1
        self.assertEqual(self.engine().verify_one(r,self.now)[0],'BAD_FORMAT')
    def test_replay_same_process(self):
        e=self.engine();r=self.receipt()
        self.assertEqual(e.verify_one(r,self.now)[0],'FRESH_HISTORY')
        self.assertEqual(e.verify_one(r,self.now)[0],'REPLAY')
    def test_replay_restart(self):
        with tempfile.TemporaryDirectory() as d:
            db=os.path.join(d,'checkpoint.db');r=self.receipt()
            e=self.engine(db=db);self.assertEqual(e.verify_one(r,self.now)[0],'FRESH_HISTORY');e.store.close()
            e2=self.engine(db=db);self.assertEqual(e2.verify_one(r,self.now)[0],'REPLAY');e2.store.close()
    def test_rollback(self):
        e=self.engine();e.verify_one(self.receipt(sequence=6),self.now)
        self.assertEqual(e.verify_one(self.receipt(sequence=5,nonce='other'),self.now)[0],'ROLLBACK')
    def test_fork(self):
        e=self.engine();e.verify_one(self.receipt(),self.now)
        self.assertEqual(e.verify_one(self.receipt(head='cd'*32,nonce='other'),self.now)[0],'SIGNED_FORK')
    def test_extension(self):
        e=self.engine();e.verify_one(self.receipt(),self.now)
        self.assertEqual(e.verify_one(self.receipt(sequence=7,nonce='other'),self.now)[0],'FRESH_HISTORY')
    def test_fresh_quorum(self):self.assertEqual(self.engine().evaluate(self.group(),self.now,6,self.head)['fresh_count'],3)
    def test_stale_count(self):self.assertEqual(self.engine().evaluate(self.group(301),self.now,6,self.head)['fresh_count'],0)
    def test_mixed(self):
        r=[self.receipt(0),self.receipt(1),self.receipt(2,age=301)]
        self.assertEqual(self.engine().evaluate(r,self.now,6,self.head)['decision'],'AUTHENTIC_HISTORIC_ONLY')
    def test_undersupported(self):self.assertEqual(self.engine().evaluate(self.group()[:2],self.now,6,self.head)['decision'],'INSUFFICIENT_FRESH_CUSTODY')
    def test_local_mismatch(self):self.assertEqual(self.engine().evaluate(self.group(),self.now,6,'cd'*32)['decision'],'LOCAL_HEAD_MISMATCH')
    def test_conflicting_sequence(self):
        r=[self.receipt(0),self.receipt(1),self.receipt(2,sequence=7)]
        self.assertEqual(self.engine().evaluate(r,self.now,6,self.head)['decision'],'CONFLICTING_CHECKPOINTS')
    def test_conflicting_head(self):
        r=[self.receipt(0),self.receipt(1),self.receipt(2,head='cd'*32)]
        self.assertEqual(self.engine().evaluate(r,self.now,6,self.head)['decision'],'CONFLICTING_CHECKPOINTS')
    def test_duplicate_root(self):
        r=self.group();r[1]=self.receipt(0,nonce='new')
        self.assertEqual(self.engine().evaluate(r,self.now,6,self.head)['rows'][1]['status'],'DUPLICATE_CUSTODY')
    def test_shared_admin(self):
        t=dict(self.trusted);t['fixture-1']=(self.keys[1].public_key(),'admin-0')
        r=make_receipt(self.keys[1],'fixture-1','admin-0',6,self.head,self.now-10,'new')
        result=FLAY165(t,self.policy).evaluate([self.receipt(0),r,self.receipt(2)],self.now,6,self.head)
        self.assertIn('DUPLICATE_CUSTODY',[x['status'] for x in result['rows']])
    def test_no_independence(self):self.assertFalse(self.engine().evaluate(self.group(),self.now,6,self.head)['independence_verified'])
    def test_no_global_completeness(self):self.assertFalse(self.engine().evaluate(self.group(),self.now,6,self.head)['global_completeness_verified'])
    def test_frozen(self):self.assertEqual(self.engine().evaluate(self.group(),self.now,6,self.head)['active_parent'],'frozen_parent')
    def test_no_learning(self):self.assertFalse(self.engine().evaluate(self.group(),self.now,6,self.head)['learning_applied'])
    def test_ledger(self):
        e=self.engine();e.evaluate(self.group(),self.now,6,self.head);self.assertEqual(e.audit(),'VALID_LOCAL_CHAIN')
    def test_ledger_tamper(self):
        e=self.engine();e.evaluate(self.group(),self.now,6,self.head);e.events[0]['result']['decision']='FAKE';self.assertEqual(e.audit(),'LOCAL_LEDGER_TAMPERED')
    def test_external_head(self):
        e=self.engine();e.evaluate(self.group(),self.now,6,self.head);self.assertEqual(e.audit('a'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_policy_age(self):
        with self.assertRaises(ValueError):Policy(max_age=-1)
    def test_policy_skew(self):
        with self.assertRaises(ValueError):Policy(future_skew=86401)
    def test_policy_quorum(self):
        with self.assertRaises(ValueError):Policy(quorum=0)
    def test_policy_bool(self):
        with self.assertRaises(ValueError):Policy(max_age=True)
    def test_empty_receipt(self):self.assertEqual(self.engine().verify_one({},self.now)[0],'BAD_FORMAT')
    def test_bad_local_sequence(self):
        with self.assertRaises(ValueError):self.engine().evaluate([],self.now,-1,self.head)

if __name__=='__main__':unittest.main(verbosity=2)
