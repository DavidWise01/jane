import unittest, tempfile
from pathlib import Path
from compromise import Registry,Policy,key,pub,sign,council,demo

class TestCompromise(unittest.TestCase):
    def setUp(self):
        self.r=Registry();self.old=key('original');self.new=key('replacement');self.a=key('council-a');self.b=key('council-b');self.c=key('council-c')
        self.r.enroll('owner',pub(self.old));self.r.steward('A',pub(self.a),'root-A');self.r.steward('B',pub(self.b),'root-B');self.r.steward('C',pub(self.c),'root-A')
    def tearDown(self):self.r.close()
    def compromise_body(self,cutoff=100,nonce='c1'):
        return {'kind':'COMPROMISE','identity':'owner','cutoff':cutoff,'reason':'fixture','nonce':nonce}
    def compromise(self,cutoff=100,nonce='c1',signers=None):
        body=self.compromise_body(cutoff,nonce);p={'A':self.a,'B':self.b} if signers is None else signers
        return self.r.declare_compromise('owner',cutoff,'fixture',council(p,body),nonce,120)
    def recovery_body(self,nonce='r1',epoch=1,at=121,new=None):
        return {'kind':'RECOVERY','identity':'owner','old_epoch':0,'new_epoch':epoch,'new_key':pub(new or self.new),'at':at,'nonce':nonce}
    def recover(self,nonce='r1',epoch=1,at=121,new=None,signers=None):
        body=self.recovery_body(nonce,epoch,at,new)
        return self.r.recover('owner',body['new_key'],epoch,at,nonce,council(signers if signers is not None else {'A':self.a,'B':self.b},body))
    def action(self,when=90,epoch=0,nonce='d1',k=None):
        body={'identity':'owner','time':when,'epoch':epoch,'nonce':nonce,'scope':'calibration'}
        return self.r.decision(body,sign(k or self.old,body))
    def test_precompromise_accept(self):self.assertEqual(self.action(),'ACCEPTED_FIXTURE')
    def test_signature_forgery(self):self.assertEqual(self.action(k=self.new),'BAD_SIGNATURE')
    def test_duplicate_decision_nonce(self):self.action();self.assertEqual(self.action(),'REPLAY')
    def test_unknown_decision_identity(self):self.assertEqual(self.r.decision({'identity':'ghost'},'00'),'INVALID_DECISION')
    def test_compromise_valid(self):self.assertEqual(self.compromise(),'COMPROMISE_RECORDED')
    def test_compromise_bad_council(self):self.assertEqual(self.compromise(signers={'A':self.a}),'INSUFFICIENT_DISTINCT_ROOTS')
    def test_shared_root(self):self.assertEqual(self.compromise(signers={'A':self.a,'C':self.c}),'INSUFFICIENT_DISTINCT_ROOTS')
    def test_forged_council(self):
        body=self.compromise_body();ats=council({'A':self.new,'B':self.b},body)
        self.assertEqual(self.r.declare_compromise('owner',100,'fixture',ats,'c1',120),'BAD_ATTESTATION')
    def test_compromise_future(self):self.assertEqual(self.compromise(cutoff=151),'INVALID_BOUNDARY')
    def test_compromise_replay(self):self.compromise();self.assertEqual(self.compromise(),'REPLAY')
    def test_double_compromise(self):self.compromise();self.assertEqual(self.compromise(nonce='c2'),'ALREADY_COMPROMISED')
    def test_reject_late_action(self):self.compromise();self.assertEqual(self.action(101),'COMPROMISED_KEY_QUARANTINED')
    def test_backdated_action_is_quarantined(self):self.compromise();self.assertEqual(self.action(99),'COMPROMISED_KEY_QUARANTINED')
    def test_grant_before_compromise(self):self.assertEqual(self.r.grant('g','owner','delegate','calibration',90),'GRANT_RECORDED')
    def test_grant_during_compromise(self):self.compromise();self.assertEqual(self.r.grant('g','owner','delegate','calibration',110),'ISSUER_QUARANTINED')
    def test_grant_lineage_review(self):self.r.grant('g','owner','delegate','calibration',90);self.compromise();self.assertEqual(self.r.grant_status('g'),'REVIEW_COMPROMISED_LINEAGE')
    def test_grant_status_unknown(self):self.assertEqual(self.r.grant_status('none'),'UNKNOWN_GRANT')
    def test_recovery_requires_compromise(self):self.assertEqual(self.recover(),'NOT_COMPROMISED')
    def test_recovery_success(self):self.compromise();self.assertEqual(self.recover(),'RECOVERED_SAME_IDENTITY')
    def test_recovery_old_key_blocked(self):self.compromise();self.recover();self.assertEqual(self.action(122),'OLD_KEY_EPOCH')
    def test_recovery_new_key_accepted(self):self.compromise();self.recover();self.assertEqual(self.action(122,1,'new',self.new),'ACCEPTED_FIXTURE')
    def test_recovery_same_key(self):self.compromise();self.assertEqual(self.recover(new=self.old),'INVALID_SUCCESSION')
    def test_recovery_skipped_epoch(self):self.compromise();self.assertEqual(self.recover(epoch=2),'INVALID_SUCCESSION')
    def test_recovery_backdated(self):self.compromise();self.assertEqual(self.recover(at=99),'INVALID_SUCCESSION')
    def test_recovery_shared_council(self):self.compromise();self.assertEqual(self.recover(signers={'A':self.a,'C':self.c}),'INSUFFICIENT_DISTINCT_ROOTS')
    def test_recovery_forged_council(self):self.compromise();self.assertEqual(self.recover(signers={'A':self.new,'B':self.b}),'BAD_ATTESTATION')
    def test_recovery_nonce_replay(self):self.compromise();self.recover();self.assertEqual(self.recover(),'REPLAY')
    def test_cannot_count_keys_as_custodians(self):self.compromise();self.assertEqual(self.r.db.execute('select count(distinct name) from identities').fetchone()[0],1)
    def test_ledger_valid(self):self.compromise();self.assertEqual(self.r.audit(),'VALID_LOCAL_CHAIN')
    def test_ledger_tamper(self):self.compromise();self.r.db.execute("update events set kind='FALSE' where seq=0");self.assertEqual(self.r.audit(),'TAMPERED')
    def test_external_head(self):self.compromise();self.assertEqual(self.r.audit('a'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_cannot_detect_valid_truncation_without_head(self):self.assertEqual(self.r.audit(),'VALID_LOCAL_CHAIN')
    def test_fixture_proof_scope(self):self.assertFalse(demo()['independence_verified'])
    def test_no_parent_activation(self):self.assertEqual(demo()['active_parent'],'frozen')
    def test_demo_flow(self):self.assertEqual(demo()['recovery'],'RECOVERED_SAME_IDENTITY')
    def test_demo_new_key(self):self.assertEqual(demo()['new_epoch_decision'],'ACCEPTED_FIXTURE')
    def test_demo_quarantine(self):self.assertEqual(demo()['quarantined'],'COMPROMISED_KEY_QUARANTINED')
    def test_demo_audit(self):self.assertEqual(demo()['audit'],'VALID_LOCAL_CHAIN')
    def test_resume_nonce_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'state.db';r=Registry(path);k=key('z');r.enroll('z',pub(k));body={'identity':'z','epoch':0,'time':0,'nonce':'persist','scope':'x'}
            self.assertEqual(r.decision(body,sign(k,body)),'ACCEPTED_FIXTURE');r.close();r=Registry(path)
            self.assertEqual(r.decision(body,sign(k,body)),'REPLAY');r.close()
    def test_initial_policy(self):
        with self.assertRaises(ValueError):Policy(recovery_quorum=1)
    def test_key_digest_determinism(self):self.assertEqual(pub(key('x')),pub(key('x')))
    def test_unauthenticated_payload(self):self.assertEqual(self.r.decision({'identity':'owner','time':0,'epoch':0,'nonce':'bad','scope':'x'},'00'),'BAD_SIGNATURE')
    def test_not_physical_proof(self):self.assertFalse(demo()['physical_compromise_verified'])
if __name__=='__main__':unittest.main(verbosity=2)