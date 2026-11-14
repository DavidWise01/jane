import os, tempfile, unittest
from beacon import Auditor, fixture, key, sign, sha, derive

class BeaconTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.f,self.r,self.a,self.t,self.now=fixture()
        self.audit=Auditor(os.path.join(self.tmp.name,'db'),self.t)
    def tearDown(self): self.audit.close(); self.tmp.cleanup()
    def evaluate(self):return self.audit.evaluate(self.f,self.r,self.a,self.now)['status']
    def test_valid(self):self.assertEqual(self.evaluate(),'FUTURE_BEACON_FIXTURE_VERIFIED')
    def test_replay(self):self.evaluate();self.assertEqual(self.evaluate(),'REPLAY_TASK')
    def test_restart(self):
        self.evaluate();self.audit.close();self.audit=Auditor(os.path.join(self.tmp.name,'db'),self.t)
        self.assertEqual(self.evaluate(),'REPLAY_TASK')
    def test_audit_chain(self):self.evaluate();self.assertTrue(self.audit.audit_log())
    def test_audit_tamper(self):
        self.evaluate();self.audit.db.execute("UPDATE events SET record='{}' WHERE seq=0");self.audit.db.commit()
        self.assertFalse(self.audit.audit_log())
    def test_no_activation(self):self.assertFalse(self.audit.evaluate(self.f,self.r,self.a,self.now)['activation'])
    def test_no_independence(self):self.assertFalse(self.audit.evaluate(self.f,self.r,self.a,self.now)['independence_verified'])
    def test_unavailable(self):self.r=None;self.assertEqual(self.evaluate(),'ROUND_UNAVAILABLE')
    def test_substitution(self):self.r=fixture('substitute')[1];self.assertEqual(self.evaluate(),'ROUND_SUBSTITUTED')
    def test_leak(self):self.r=fixture('leaked')[1];self.assertEqual(self.evaluate(),'PREMATURE_BEACON_RELEASE_REPORTED')
    def test_stale(self):self.now=1000;self.assertEqual(self.evaluate(),'STALE_BEACON')
    def test_future(self):self.now=100;self.assertEqual(self.evaluate(),'BEACON_FROM_FUTURE')
    def test_modified_randomness(self):self.r['body']['randomness']=sha('forgery');self.assertEqual(self.evaluate(),'BAD_BEACON_SIGNATURE')
    def test_bad_beacon_signer(self):self.r=sign(key('bad'),self.r['body']);self.assertEqual(self.evaluate(),'BAD_BEACON_SIGNATURE')
    def test_bad_task_signer(self):self.f=sign(key('bad'),self.f['body']);self.assertEqual(self.evaluate(),'BAD_FREEZE_SIGNATURE')
    def test_bad_task_format(self):self.f=sign(key('task'),dict(self.f['body'],target_round=0));self.assertEqual(self.evaluate(),'BAD_FREEZE_FORMAT')
    def test_bad_task_order(self):self.f=sign(key('task'),dict(self.f['body'],tick=200));self.assertEqual(self.evaluate(),'BAD_FREEZE_FORMAT')
    def test_bad_anchor_signature(self):self.a[0]['signature']='00';self.assertEqual(self.evaluate(),'BAD_ANCHOR_SIGNATURE')
    def test_anchor_mismatch(self):self.a[0]=sign(key('anchor-a'),dict(self.a[0]['body'],beacon_commitment='a'*64));self.assertEqual(self.evaluate(),'ANCHOR_MISMATCH')
    def test_anchor_claimed_early(self):self.a[0]=sign(key('anchor-a'),dict(self.a[0]['body'],observed_tick=200));self.assertEqual(self.evaluate(),'ANCHOR_BEFORE_BEACON_REPORTED')
    def test_anchor_claimed_future(self):self.a[0]=sign(key('anchor-a'),dict(self.a[0]['body'],observed_tick=400));self.assertEqual(self.evaluate(),'ANCHOR_FROM_FUTURE')
    def test_insufficient(self):self.a=self.a[:1];self.assertEqual(self.evaluate(),'INSUFFICIENT_DECLARED_ANCHORS')
    def test_three_keys_one_admin(self):
        self.t=self.t.__class__(self.t.task_key,self.t.beacon_keys,{x:(y[0],'single') for x,y in self.t.anchor_keys.items()},2)
        self.audit.close();self.audit=Auditor(os.path.join(self.tmp.name,'db'),self.t)
        self.assertEqual(self.evaluate(),'INSUFFICIENT_DECLARED_ANCHORS')
    def test_anchor_duplication(self):self.a=[self.a[0]]*3;self.assertEqual(self.evaluate(),'INSUFFICIENT_DECLARED_ANCHORS')
    def test_different_task_challenge(self):self.assertNotEqual(derive(sha('a'),'fixture-beacon',42,sha('r')),derive(sha('b'),'fixture-beacon',42,sha('r')))
    def test_different_round_challenge(self):self.assertNotEqual(derive(sha('a'),'fixture-beacon',42,sha('r')),derive(sha('a'),'fixture-beacon',43,sha('r')))
    def test_invalid_challenge_digest(self):
        with self.assertRaises(ValueError):derive('bad','fixture-beacon',42,sha('r'))
    def test_unknown_beacon(self):self.f=sign(key('task'),dict(self.f['body'],beacon_id='unknown'));self.assertEqual(self.evaluate(),'BAD_FREEZE_FORMAT')
    def test_freeze_after_release(self):
        self.f=sign(key('task'),dict(self.f['body'],tick=230,not_before=250))
        self.assertEqual(self.evaluate(),'PREMATURE_BEACON_RELEASE_REPORTED')
    def test_beacon_equivocation(self):
        self.evaluate()
        changed=sign(key('beacon'),dict(self.r['body'],randomness=sha('alternate')))
        replacement=[sign(key('anchor-'+w),dict(self.a[i]['body'],beacon_commitment=sha(changed))) for i,w in enumerate(('a','b','c'))]
        self.f=sign(key('task'),dict(self.f['body'],task_hash=sha('different-task')))
        self.r=changed;self.a=replacement
        self.assertEqual(self.evaluate(),'SIGNED_BEACON_EQUIVOCATION')
    def test_frozen_round_protection(self):
        self.f=sign(key('task'),dict(self.f['body'],target_round=43))
        self.assertEqual(self.evaluate(),'ROUND_SUBSTITUTED')
    def test_wrong_anchor_beacon(self):
        self.a[0]=sign(key('anchor-a'),dict(self.a[0]['body'],beacon_id='different'))
        self.assertEqual(self.evaluate(),'ANCHOR_MISMATCH')
    def test_bad_now(self):self.now=-1;self.assertEqual(self.evaluate(),'BAD_EVALUATION_TIME')
    def test_deterministic_fixture(self):self.assertEqual(fixture()[0],fixture()[0])
    def test_missing_anchor(self):self.a=[];self.assertEqual(self.evaluate(),'INSUFFICIENT_DECLARED_ANCHORS')

if __name__=='__main__':unittest.main(verbosity=2)