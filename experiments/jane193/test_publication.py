import unittest, tempfile, os, copy
from publication import fixture, FLAY, hashof, signed, DOMAIN, Audit
class TestPublication(unittest.TestCase):
    def setUp(self):
        self.priv,self.tr,self.task,self.obs,self.beacon,self.attempt=fixture()
        self.f=FLAY(self.tr)
    def tearDown(self):self.f.close()
    def status(self,*a,**k):return self.f.check(self.task,*a,**k)['status']
    def test_published(self):self.assertEqual(self.status([self.attempt('SUCCESS')],[self.obs('a','PUBLISHED','pub-aaaa'),self.obs('b','PUBLISHED','pub-bbbb')],self.beacon),'PUBLISHED_FIXTURE_OBSERVED')
    def test_replay(self):
        o=[self.obs('a','NOT_OBSERVED','nonce-aaaa')]
        self.f.check(self.task,[],o)
        self.assertEqual(self.status([],o),'REPLAY')
    def test_replay_after_restart(self):
        with tempfile.TemporaryDirectory() as td:
            p=os.path.join(td,'a.sqlite');f=FLAY(self.tr,p);o=[self.obs('a','NOT_OBSERVED','persist-aaa')];f.check(self.task,[],o);f.close()
            f=FLAY(self.tr,p);self.assertEqual(f.check(self.task,[],o)['status'],'REPLAY');f.close()
    def test_missing(self):self.assertEqual(self.status([],[self.obs('a','NOT_OBSERVED','missing-aaa'),self.obs('b','NOT_OBSERVED','missing-bbb')]),'NOT_OBSERVED_BY_FIXTURE_QUORUM')
    def test_outage(self):self.assertEqual(self.status([self.attempt()],[]),'NETWORK_UNAVAILABLE_OR_WITHHELD')
    def test_conflict(self):self.assertEqual(self.status([],[self.obs('a','PUBLISHED','conflict-a'),self.obs('b','NOT_OBSERVED','conflict-b')]),'AVAILABILITY_CONFLICT')
    def test_missing_not_malice(self):self.assertFalse(self.f.check(self.task,[self.attempt()],[])['evidence']['intent_established'])
    def test_before_deadline(self):self.assertEqual(self.status([],[],now=100),'BEFORE_PUBLICATION_DEADLINE')
    def test_no_fallback_round(self):
        t=copy.deepcopy(self.task);t['round']=43
        self.assertEqual(self.f.check(t,[],[self.obs('a','PUBLISHED','other-round')])['status'],'OBSERVATION_CONTEXT_MISMATCH')
    def test_beacon_bad_signature(self):
        b=copy.deepcopy(self.beacon);b['sig']='00'*64
        self.assertEqual(self.status([],[],b),'BAD_BEACON_SIGNATURE')
    def test_bad_observer_signature(self):
        o=self.obs('a','NOT_OBSERVED','bad-sig-aaaa');o['data']['time']=123
        self.assertEqual(self.status([],[o]),'BAD_OBSERVER_SIGNATURE')
    def test_duplicate_actor(self):self.assertEqual(self.status([],[self.obs('a','NOT_OBSERVED','dupe-aaaa'),self.obs('a','NOT_OBSERVED','dupe-bbbb')]),'DUPLICATE_OBSERVER')
    def test_shared_admin(self):
        t=copy.deepcopy(self.tr.admins);t['b']=t['a'];f=FLAY(type(self.tr)(self.tr.keys,t,self.tr.roots));self.assertEqual(f.check(self.task,[],[self.obs('a','NOT_OBSERVED','root-aaaa'),self.obs('b','NOT_OBSERVED','root-bbbb')])['status'],'SHARED_DECLARED_ANCESTRY');f.close()
    def test_shared_root(self):
        t=copy.deepcopy(self.tr.roots);t['b']=t['a'];f=FLAY(type(self.tr)(self.tr.keys,self.tr.admins,t));self.assertEqual(f.check(self.task,[],[self.obs('a','NOT_OBSERVED','root-aaaa'),self.obs('b','NOT_OBSERVED','root-bbbb')])['status'],'SHARED_DECLARED_ANCESTRY');f.close()
    def test_stale_publication(self):
        self.assertEqual(self.status([],[self.obs('a','PUBLISHED','onlyaaaa')],self.beacon),'INSUFFICIENT_PUBLICATION_CUSTODY')
    def test_publication_without_content(self):self.assertEqual(self.status([],[self.obs('a','PUBLISHED','no-content')]),'PUBLICATION_REPORTED_CONTENT_UNAVAILABLE')
    def test_bad_output_hash(self):
        o=self.obs('a','PUBLISHED','bad-output-1',output='different');o2=self.obs('b','PUBLISHED','bad-output-2')
        self.assertEqual(self.status([],[o,o2],self.beacon),'BEACON_OUTPUT_CONFLICT')
    def test_not_observed_no_custody(self):self.assertEqual(self.status([],[self.obs('a','NOT_OBSERVED','single-aaa')]),'INSUFFICIENT_AVAILABILITY_EVIDENCE')
    def test_invalid_task(self):
        t=copy.deepcopy(self.task);t['domain']='WRONG'
        self.assertEqual(self.f.check(t,[],[])['status'],'INVALID_FROZEN_TASK')
    def test_invalid_fetch(self):
        a=self.attempt();a['round']=45
        self.assertEqual(self.status([a],[]),'INVALID_FETCH_ATTEMPT')
    def test_future_obs(self):self.assertEqual(self.status([],[self.obs('a','NOT_OBSERVED','future-aaa',time=500)]),'INVALID_OBSERVATION')
    def test_weak_nonce(self):self.assertEqual(self.status([],[self.obs('a','NOT_OBSERVED','a')]),'INVALID_NONCE')
    def test_budget(self):self.assertEqual(self.status([self.attempt()]*33,[]),'EVIDENCE_BUDGET_EXCEEDED')
    def test_audit(self):self.f.check(self.task,[],[]);self.assertEqual(self.f.audit.check(),'VALID_LOCAL_CHAIN')
    def test_audit_external_head(self):self.f.check(self.task,[],[]);self.assertEqual(self.f.audit.check('f'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_audit_tamper(self):
        self.f.check(self.task,[],[]);self.f.audit.db.execute("UPDATE events SET payload='{}' WHERE id=1");self.f.audit.db.commit()
        self.assertEqual(self.f.audit.check(),'TAMPERED')
    def test_retains_frozen_parent(self):self.assertEqual(self.f.check(self.task,[],[])['active'],'FROZEN_PARENT')
    def test_not_real_independence(self):self.assertFalse(self.f.check(self.task,[],[])['independent_operators_verified'])
    def test_no_automatic_learning(self):self.assertFalse(self.f.check(self.task,[],[])['learning_applied'])
    def test_signed_output_round(self):
        b=copy.deepcopy(self.beacon);b['data']['round']=43
        self.assertEqual(self.status([],[],b),'BAD_BEACON_SIGNATURE')
    def test_signed_wrong_context(self):
        d=copy.deepcopy(self.beacon['data']);d['round']=43;b=signed(self.priv['beacon'],d)
        self.assertEqual(self.status([],[],b),'BEACON_CONTEXT_MISMATCH')
    def test_deterministic_task_hash(self):self.assertEqual(hashof(self.task),hashof(dict(reversed(list(self.task.items())))))
    def test_audit_chain_survives_restart(self):
        with tempfile.TemporaryDirectory() as td:
            p=os.path.join(td,'b.sqlite');f=FLAY(self.tr,p);f.check(self.task,[],[]);head=f.audit.head();f.close()
            f=FLAY(self.tr,p);self.assertEqual(f.audit.check(head),'VALID_LOCAL_CHAIN');f.close()
if __name__=='__main__':unittest.main(verbosity=2)