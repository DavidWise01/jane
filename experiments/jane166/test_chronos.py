import tempfile,unittest,os
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from chronos import Chronos,signed_claim,temporal_relation,causal_audit,fixture

class TestChronos(unittest.TestCase):
    def setUp(self):
        self.keys=[Ed25519PrivateKey.from_private_bytes(bytes([i])*32) for i in (11,12,13)]
        self.auth={f'key{i}':(k.public_key().public_bytes_raw(),f'root{i}',f'admin{i}') for i,k in enumerate(self.keys)}
        self.f=Chronos(self.auth)
    def tearDown(self):self.f.close()
    def claim(self,i=0,t=100,u=5,nonce=None,obs='o'):
        return signed_claim(self.keys[i],f'root{i}',f'admin{i}',f'clock{i}',obs,t,u,nonce or f'n{i}-{t}-{obs}','key'+str(i))
    def test_accept(self):self.assertEqual(self.f.ingest(self.claim()),'ACCEPTED')
    def test_replay(self):
        c=self.claim();self.f.ingest(c);self.assertEqual(self.f.ingest(c),'REPLAY')
    def test_signature_tampered(self):
        from dataclasses import replace
        c=self.claim();self.assertEqual(self.f.ingest(replace(c,nominal_ms=777)),'BAD_SIGNATURE')
    def test_bad_signature_text(self):
        from dataclasses import replace
        self.assertEqual(self.f.ingest(replace(self.claim(),signature='xx')),'BAD_SIGNATURE')
    def test_unknown(self):
        from dataclasses import replace
        self.assertEqual(self.f.ingest(replace(self.claim(),key_id='other')),'UNKNOWN_KEY')
    def test_admin_mismatch(self):
        from dataclasses import replace
        self.assertEqual(self.f.ingest(replace(self.claim(),admin='someone')),'IDENTITY_MISMATCH')
    def test_root_mismatch(self):
        from dataclasses import replace
        self.assertEqual(self.f.ingest(replace(self.claim(),root='other')),'IDENTITY_MISMATCH')
    def test_negative_uncertainty(self):
        c=self.claim(u=-1);self.assertEqual(self.f.ingest(c),'BAD_UNCERTAINTY')
    def test_high_uncertainty(self):
        c=self.claim(u=10001);self.assertEqual(self.f.ingest(c),'BAD_UNCERTAINTY')
    def test_bool_not_time(self):
        c=self.claim(t=True);self.assertEqual(self.f.ingest(c),'BAD_UNCERTAINTY')
    def test_bool_not_uncertainty(self):
        c=self.claim(u=True);self.assertEqual(self.f.ingest(c),'BAD_UNCERTAINTY')
    def test_zero_uncertainty(self):self.assertEqual(self.f.ingest(self.claim(u=0)),'ACCEPTED')
    def test_interval(self):self.assertEqual(self.claim(t=100,u=9).interval(),[91,109])
    def test_matching_quorum(self):
        cs=[self.claim(i,t=100+i,u=8) for i in range(3)]
        for c in cs:self.f.ingest(c)
        self.assertEqual(self.f.compare(cs,'o')['status'],'MATCHED_FIXTURE_INTERVAL')
    def test_intersection(self):
        cs=[self.claim(i,t=100+i,u=8) for i in range(3)]
        for c in cs:self.f.ingest(c)
        self.assertEqual(self.f.compare(cs,'o')['intersection'],[94,108])
    def test_disjoint_conflict(self):
        cs=[self.claim(i,t=100+i*100,u=2) for i in range(3)]
        for c in cs:self.f.ingest(c)
        self.assertEqual(self.f.compare(cs)['status'],'CLOCK_CONFLICT')
    def test_no_average(self):
        cs=[self.claim(i,t=i*100,u=1) for i in range(3)]
        for c in cs:self.f.ingest(c)
        self.assertIsNone(self.f.compare(cs)['intersection'])
    def test_insufficient(self):
        c=self.claim();self.f.ingest(c);self.assertEqual(self.f.compare([c])['status'],'INSUFFICIENT_OR_DISPUTED_CUSTODY')
    def test_duplicate_root(self):
        a=self.claim();b=self.claim(nonce='new');self.f.ingest(a);self.f.ingest(b)
        self.assertIn('SHARED_CUSTODY',self.f.compare([a,b])['failures'])
    def test_duplicate_admin(self):
        from dataclasses import replace
        cs=[self.claim(0),self.claim(1)]
        self.f.authorities['key1']=(self.auth['key1'][0],'root1','admin0')
        cs[1]=signed_claim(self.keys[1],'root1','admin0','clock1','o',100,5,'new','key1')
        for c in cs:self.f.ingest(c)
        self.assertIn('SHARED_CUSTODY',self.f.compare(cs)['failures'])
    def test_observation_mismatch(self):
        c=self.claim();self.f.ingest(c)
        self.assertEqual(self.f.compare([c],observation='else')['status'],'NO_ADMISSIBLE_CLAIMS')
    def test_not_ingested(self):self.assertEqual(self.f.compare([self.claim()])['status'],'NO_ADMISSIBLE_CLAIMS')
    def test_no_evidence(self):self.assertEqual(self.f.compare([])['status'],'NO_EVIDENCE')
    def test_not_real_independence(self):
        cs=[self.claim(i,t=100,u=10) for i in range(3)]
        for c in cs:self.f.ingest(c)
        self.assertFalse(self.f.compare(cs)['independent_operators_verified'])
    def test_before(self):self.assertEqual(temporal_relation([1,2],[3,4]),'DEFINITELY_BEFORE')
    def test_after(self):self.assertEqual(temporal_relation([3,4],[1,2]),'DEFINITELY_AFTER')
    def test_touching_overlap(self):self.assertEqual(temporal_relation([1,2],[2,4]),'OVERLAP_UNORDERED')
    def test_nested_overlap(self):self.assertEqual(temporal_relation([0,10],[3,4]),'OVERLAP_UNORDERED')
    def test_causal_consistent(self):self.assertEqual(causal_audit([1,2],[3,4])['status'],'TEMPORAL_CONSISTENT')
    def test_causal_ambiguous(self):self.assertEqual(causal_audit([1,3],[2,4])['status'],'TEMPORAL_AMBIGUOUS')
    def test_causal_contradiction(self):self.assertEqual(causal_audit([5,6],[1,2])['status'],'CLOCK_CAUSAL_CONTRADICTION')
    def test_no_causal_edge(self):self.assertEqual(causal_audit([5,6],[1,2],False)['status'],'NO_CAUSAL_EDGE')
    def test_audit(self):self.f.ingest(self.claim());self.assertEqual(self.f.audit_chain(),'VALID_LOCAL_AUDIT')
    def test_external_head_mismatch(self):self.f.ingest(self.claim());self.assertEqual(self.f.audit_chain('f'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_audit_tamper(self):
        self.f.ingest(self.claim());self.f.db.execute("UPDATE audit SET event='{}'");self.f.db.commit()
        self.assertEqual(self.f.audit_chain(),'TAMPERED_LOCAL_AUDIT')
    def test_restart_replay(self):
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,'db.sqlite');a=Chronos(self.auth,path);c=self.claim();a.ingest(c);a.close()
            b=Chronos(self.auth,path);self.assertEqual(b.ingest(c),'REPLAY');b.close()
    def test_restart_audit(self):
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,'db.sqlite');a=Chronos(self.auth,path);a.ingest(self.claim());head=a.audit_head();a.close()
            b=Chronos(self.auth,path);self.assertEqual(b.audit_chain(head),'VALID_LOCAL_AUDIT');b.close()
    def test_fixture(self):self.assertEqual(fixture()['matching']['status'],'MATCHED_FIXTURE_INTERVAL')
    def test_fixture_conflict(self):self.assertEqual(fixture()['disagreement']['status'],'CLOCK_CONFLICT')
    def test_parent_frozen(self):self.assertEqual(fixture()['active'],'frozen_parent')
    def test_no_learning(self):self.assertFalse(fixture()['learning_applied'])

if __name__=='__main__':unittest.main(verbosity=2)
