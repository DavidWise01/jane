import unittest, tempfile, os, copy
from custody import *

class TestCustody(unittest.TestCase):
    def setUp(self):
        self.p,self.keys,self.priv=fixture()
        self.ledger=Ledger()
        self.f=FLAY213(self.keys,self.ledger)
    def tearDown(self):self.ledger.close()
    def test_valid(self):self.assertEqual(self.f.inspect(self.p)['verdict'],'DECLARED_CUSTODY_CONSISTENT_FIXTURE')
    def test_roots(self):
        p,k,_=fixture('shared_root');self.assertEqual(FLAY213(k,self.ledger).inspect(p)['verdict'],'SHARED_ANCESTRY_WITHHELD')
    def test_operators(self):
        p,k,_=fixture('shared_operator');self.assertEqual(FLAY213(k,self.ledger).inspect(p)['verdict'],'SHARED_ANCESTRY_WITHHELD')
    def test_sensors(self):
        p,k,_=fixture('shared_sensor');self.assertEqual(FLAY213(k,self.ledger).inspect(p)['verdict'],'INSUFFICIENT_INDEPENDENT_OBSERVATION')
    def test_logger(self):
        p,k,_=fixture('shared_logger');self.assertEqual(FLAY213(k,self.ledger).inspect(p)['verdict'],'SHARED_ANCESTRY_WITHHELD')
    def test_conflict(self):
        p,k,_=fixture('conflict');self.assertEqual(FLAY213(k,self.ledger).inspect(p)['verdict'],'CHECKPOINT_DISAGREEMENT')
    def test_clock(self):
        p,k,_=fixture('bad_clock');self.assertEqual(FLAY213(k,self.ledger).inspect(p)['verdict'],'INVALID_CHRONOLOGY')
    def test_replay(self):self.f.inspect(self.p);self.assertEqual(self.f.inspect(self.p)['verdict'],'REPLAY')
    def test_no_witness(self):
        p=copy.deepcopy(self.p);p['witnesses']=[];self.assertEqual(self.f.inspect(p)['verdict'],'MISSING_WITNESSES')
    def test_forged_witness(self):
        p=copy.deepcopy(self.p);p['witnesses'][0]['body']['sensor']='fake';self.assertEqual(self.f.inspect(p)['verdict'],'SIGNATURE_INVALID')
    def test_forged_counter(self):
        p=copy.deepcopy(self.p);p['counter']['body']['sequence']=5;self.assertEqual(self.f.inspect(p)['verdict'],'SIGNATURE_INVALID')
    def test_fake_key(self):
        p=copy.deepcopy(self.p);k=dict(self.keys);k['witnessA']=self.priv['witnessB'].public_key();self.assertEqual(FLAY213(k,self.ledger).inspect(p)['verdict'],'SIGNATURE_INVALID')
    def test_unknown_key(self):
        k=dict(self.keys);k.pop('witnessA');self.assertEqual(FLAY213(k,self.ledger).inspect(self.p)['verdict'],'SIGNATURE_INVALID')
    def test_dup_id(self):
        p=copy.deepcopy(self.p);p['witnesses'][0]=p['counter'];self.assertEqual(self.f.inspect(p)['verdict'],'DUPLICATE_IDENTITY')
    def test_short_nonce(self):
        p=copy.deepcopy(self.p);p['counter']['body']['nonce']='short';self.assertEqual(self.f.inspect(p)['verdict'],'INVALID_NONCE')
    def test_bad_sequence(self):
        p,k,s=fixture();b=p['counter']['body'];b['sequence']=0;p['counter']=signed(b,s['executor']);self.assertEqual(FLAY213(k,self.ledger).inspect(p)['verdict'],'INVALID_SEQUENCE')
    def test_negative_clock(self):
        p,k,s=fixture();b=p['counter']['body'];b['tick']=-2;p['counter']=signed(b,s['executor']);self.assertEqual(FLAY213(k,self.ledger).inspect(p)['verdict'],'INVALID_CHRONOLOGY')
    def test_missing_custody(self):
        p,k,s=fixture();b=p['witnesses'][0]['body'];b.pop('sensor');p['witnesses'][0]=signed(b,s['witnessA']);self.assertEqual(FLAY213(k,self.ledger).inspect(p)['verdict'],'MISSING_CUSTODY_DECLARATION')
    def test_bad_head(self):
        p,k,s=fixture();b=p['counter']['body'];b['head']='bad';p['counter']=signed(b,s['executor']);self.assertEqual(FLAY213(k,self.ledger).inspect(p)['verdict'],'INVALID_HEAD')
    def test_bad_hash_chain(self):
        self.f.inspect(self.p);self.ledger.db.execute("UPDATE audit SET digest='bad' WHERE seq=1");self.ledger.db.commit();self.assertEqual(self.f.inspect(self.p)['verdict'],'CORRUPT_AUDIT')
    def test_persistent_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            path=os.path.join(folder,'audit.db');a=Ledger(path);self.assertEqual(FLAY213(self.keys,a).inspect(self.p)['verdict'],'DECLARED_CUSTODY_CONSISTENT_FIXTURE');a.close();b=Ledger(path);self.assertEqual(FLAY213(self.keys,b).inspect(self.p)['verdict'],'REPLAY');b.close()
    def test_parent_frozen(self):self.assertEqual(demo()['parent'],'FROZEN')
    def test_deterministic_digest(self):self.assertEqual(digest({'b':2,'a':1}),digest({'a':1,'b':2}))
    def test_tamper_signature(self):
        p=copy.deepcopy(self.p);p['witnesses'][0]['signature']='bad';self.assertEqual(self.f.inspect(p)['verdict'],'SIGNATURE_INVALID')
    def test_different_nonce(self):
        self.f.inspect(self.p);p,k,_=fixture(nonce='jane213-newnonce-0002');self.assertEqual(FLAY213(k,self.ledger).inspect(p)['verdict'],'DECLARED_CUSTODY_CONSISTENT_FIXTURE')
    def test_audit_chain_valid(self):
        self.f.inspect(self.p);self.assertTrue(self.ledger.audit_ok())
    def test_invalid_packet(self):self.assertEqual(self.f.inspect({})['verdict'],'INVALID_PACKET')
    def test_no_automatic_activation(self):self.assertNotIn('ACTIVATED',str(demo()))

if __name__=='__main__':unittest.main()