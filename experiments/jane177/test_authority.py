import os
import tempfile
import unittest
from authority import Authority,Gate,keypair,sign,demo,sha

class AuthorityTests(unittest.TestCase):
    def setUp(self):
        self.sk,self.pub=keypair('steward-test')
        self.alice=Authority('alice',('calibration.clock',),0,1000,self.pub,'fixture-root-a')
        self.g=Gate(authority=(self.alice,))
        self.e=dict(original=1000,repeat=1003,scope='calibration.clock')
        self.p=dict(principal='alice',scope='calibration.clock',parent_digest=self.g.frozen_digest,
          new_policy=dict(version='v2',scope='calibration.clock',tolerance=2),
          effective_at=150,expires_at=300,reason='strict comparator',nonce='one')
    def runp(self,changes=None,signature=None,nonce=None,g=None):
        p={**self.p,**(changes or {})};g=g or self.g
        return g.propose(p,signature if signature is not None else sign(self.sk,p),nonce or p.get('nonce'),self.e)
    def test_baseline(self):self.assertEqual(demo()[1]['status'],'AUTHORIZED_REPLAY')
    def test_policy_diff(self):self.assertTrue(self.runp()['policy_induced_change'])
    def test_old(self):self.assertEqual(self.runp()['old_verdict'],'ACCEPT')
    def test_new(self):self.assertEqual(self.runp()['new_verdict'],'REJECT')
    def test_frozen(self):self.assertEqual(self.runp()['active_policy'],self.g.frozen_digest)
    def test_no_activation(self):self.assertFalse(self.runp()['policy_activated'])
    def test_no_independence(self):self.assertFalse(self.runp()['independent_authority_verified'])
    def test_good_signature(self):self.assertEqual(self.runp()['status'],'AUTHORIZED_REPLAY')
    def test_bad_signature(self):self.assertEqual(self.runp(signature='00')['status'],'INVALID_SIGNATURE')
    def test_wrong_signer(self):
        other,_=keypair('other');self.assertEqual(self.runp(signature=sign(other,self.p))['status'],'INVALID_SIGNATURE')
    def test_unknown_authority(self):self.assertEqual(self.runp({'principal':'unknown'})['status'],'UNKNOWN_AUTHORITY')
    def test_scope(self):self.assertEqual(self.runp({'scope':'other'})['status'],'OUT_OF_SCOPE')
    def test_future(self):self.assertEqual(self.runp({'effective_at':201})['status'],'NOT_YET_EFFECTIVE')
    def test_expired(self):self.assertEqual(self.runp({'expires_at':199})['status'],'POLICY_EXPIRED')
    def test_invalid_window(self):self.assertEqual(self.runp({'effective_at':300,'expires_at':200})['status'],'BAD_TIME_RANGE')
    def test_grant_expired(self):
        a=Authority('alice',('calibration.clock',),0,100,self.pub,'fixture-root-a')
        g=Gate(authority=(a,));self.assertEqual(self.runp(g=g)['status'],'AUTHORITY_EXPIRED')
    def test_grant_future(self):
        a=Authority('alice',('calibration.clock',),300,1000,self.pub,'fixture-root-a')
        g=Gate(authority=(a,));self.assertEqual(self.runp(g=g)['status'],'AUTHORITY_EXPIRED')
    def test_exceeds_grant(self):self.assertEqual(self.runp({'expires_at':1200})['status'],'BAD_TIME_RANGE')
    def test_before_grant(self):self.assertEqual(self.runp({'effective_at':-1})['status'],'BAD_TIME_RANGE')
    def test_wrong_parent(self):self.assertEqual(self.runp({'parent_digest':'a'*64})['status'],'WRONG_PREDECESSOR')
    def test_changed_scope_of_policy(self):
        self.assertEqual(self.runp({'new_policy':dict(version='v2',scope='other',tolerance=2)})['status'],'BAD_POLICY')
    def test_negative_tolerance(self):
        self.assertEqual(self.runp({'new_policy':dict(version='v2',scope='calibration.clock',tolerance=-1)})['status'],'BAD_POLICY')
    def test_huge_tolerance(self):
        self.assertEqual(self.runp({'new_policy':dict(version='v2',scope='calibration.clock',tolerance=1001)})['status'],'BAD_POLICY')
    def test_float_tolerance(self):
        self.assertEqual(self.runp({'new_policy':dict(version='v2',scope='calibration.clock',tolerance=2.0)})['status'],'BAD_POLICY')
    def test_malformed(self):
        p={**self.p,'extra':True};self.assertEqual(self.g.propose(p,sign(self.sk,p),'one',self.e)['status'],'MALFORMED_PROPOSAL')
    def test_nonce_mismatch(self):self.assertEqual(self.runp(nonce='wrong')['status'],'NONCE_MISMATCH')
    def test_replay(self):
        self.runp();self.assertEqual(self.runp()['status'],'REPLAY_NONCE')
    def test_bad_signature_cannot_burn_nonce(self):
        self.runp(signature='bad');self.assertEqual(self.runp()['status'],'AUTHORIZED_REPLAY')
    def test_denied_signed_nonce_burned(self):
        self.runp({'effective_at':201});self.assertEqual(self.runp({'effective_at':201})['status'],'REPLAY_NONCE')
    def test_conflicting_revision(self):
        self.runp();p={'nonce':'two','new_policy':dict(version='v3',scope='calibration.clock',tolerance=1)}
        self.assertEqual(self.runp(p)['status'],'CONFLICTING_REVISION')
    def test_same_revision_new_nonce_conflict(self):
        self.runp();self.assertEqual(self.runp({'nonce':'two'})['status'],'CONFLICTING_REVISION')
    def test_deterministic_digest(self):self.assertEqual(sha(self.e),sha(dict(scope='calibration.clock',repeat=1003,original=1000)))
    def test_audit(self):self.runp();self.assertEqual(self.g.audit(),'LOCAL_CHAIN_VALID')
    def test_tamper(self):
        self.runp();self.g.conn.execute("UPDATE decisions SET kind='FAKE' WHERE seq=1")
        self.assertEqual(self.g.audit(),'LEDGER_TAMPER')
    def test_external_anchor(self):self.assertEqual(self.g.audit('b'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_deny_logged(self):
        self.runp(signature='00');self.assertEqual(self.g.conn.execute('SELECT count(*) FROM decisions').fetchone()[0],1)
    def test_restart_nonce(self):
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,'audit.sqlite')
            g=Gate(path,(self.alice,));self.runp(g=g);g.conn.close()
            h=Gate(path,(self.alice,));self.assertEqual(self.runp(g=h)['status'],'REPLAY_NONCE')
    def test_restart_revision(self):
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,'audit.sqlite')
            g=Gate(path,(self.alice,));self.runp(g=g);g.conn.close()
            h=Gate(path,(self.alice,));self.assertEqual(self.runp({'nonce':'two'},g=h)['status'],'CONFLICTING_REVISION')
    def test_report_scope_mismatch(self):
        e={**self.e,'scope':'other'}
        self.assertEqual(self.g.propose(self.p,sign(self.sk,self.p),'one',e)['status'],'EVIDENCE_SCOPE_MISMATCH')
    def test_missing_authority(self):
        g=Gate();self.assertEqual(self.runp(g=g)['status'],'UNKNOWN_AUTHORITY')
    def test_demo_audit(self):self.assertEqual(demo()[0].audit(),'LOCAL_CHAIN_VALID')
    def test_unchanged_verdict(self):
        self.assertFalse(self.runp({'new_policy':dict(version='v2',scope='calibration.clock',tolerance=4)})['policy_induced_change'])
    def test_policy_digest(self):self.assertEqual(len(self.runp()['policy_digest']),64)
    def test_evidence_digest(self):self.assertEqual(self.runp()['evidence_digest'],sha(self.e))
    def test_custody_is_fixture(self):self.assertEqual(self.runp()['authority_ancestry'],'fixture-root-a')

if __name__=='__main__':unittest.main(verbosity=2)