import json
import os
import tempfile
import unittest
from collusion import Policy,FLAY204,Reject,digest,fixture

class Tests(unittest.TestCase):
    def setUp(self):
        self.p=Policy('holdout-204',12,8,8,('ada','bert','clio'))
        self.f=FLAY204(self.p)
    def tearDown(self): self.f.ledger.close()
    def send(self,ident='one',agent='ada',recipient='collect',subset=(0,1),credits=3,roots=None,payload=None):
        return self.f.release(ident,agent,recipient,subset,credits,{'score':ident} if payload is None else payload,roots)
    def deny(self,code,**kwargs):
        with self.assertRaises(Reject) as ctx: self.send(**kwargs)
        self.assertEqual(ctx.exception.code,code)
    def test_clean(self): self.assertEqual(self.send()['verdict'],'RELEASE_RECORDED_FIXTURE')
    def test_no_events(self): self.assertEqual(self.f.audit()['events'],0)
    def test_counts(self): self.send(); self.assertEqual(self.f.audit()['global_credits'],3)
    def test_agent_count(self): self.send();self.assertEqual(self.f.audit()['agents']['ada'],3)
    def test_recipient_count(self): self.send();self.assertEqual(self.f.audit()['recipient_groups']['collect']['credits'],3)
    def test_union(self): self.send();self.send('two','bert','collect',(1,2),2);self.assertEqual(self.f.audit()['recipient_groups']['collect']['union_subset'],[0,1,2])
    def test_agents(self): self.send();self.send('two','bert','collect',(1,2),2);self.assertEqual(self.f.audit()['recipient_groups']['collect']['agents'],['ada','bert'])
    def test_common_root(self): self.send();self.send('two','bert','collect',(1,2),2);self.assertEqual(self.f.audit()['recipient_groups']['collect']['shared_roots'],['holdout-204'])
    def test_not_independent(self): self.send(roots=['holdout-204','upstream']);self.send('two','bert','collect',(1,2),2,['holdout-204','upstream']);self.assertIn('upstream',self.f.audit()['recipient_groups']['collect']['shared_roots'])
    def test_recipient_reject(self): self.send(credits=5);self.deny('RECIPIENT_BUDGET_EXCEEDED',ident='two',agent='bert',credits=4)
    def test_global_reject(self): self.send(credits=8);self.send('two','bert','other',(2,),4);self.deny('GLOBAL_BUDGET_EXCEEDED',ident='three',agent='clio',recipient='third',credits=1)
    def test_agent_reject(self): self.send(credits=5);self.deny('AGENT_BUDGET_EXCEEDED',ident='two',recipient='other',credits=4)
    def test_budgets_equal_allow(self): self.send(credits=8);self.send('two','bert','other',(2,),4);self.assertEqual(self.f.audit()['global_credits'],12)
    def test_rejected_atomic(self): self.send(credits=5);self.deny('RECIPIENT_BUDGET_EXCEEDED',ident='two',agent='bert',credits=4);self.assertEqual(self.f.audit()['events'],1)
    def test_replay(self): self.send();self.deny('REPLAY')
    def test_different_ids_same_payload_charged(self): self.send(payload={'v':1});self.send('two','bert','other',(0,1),3,payload={'v':1});self.assertEqual(self.f.audit()['distinct_payloads'],1);self.assertEqual(self.f.audit()['global_credits'],6)
    def test_noncanonical_subset(self):self.deny('NONCANONICAL_SUBSET',subset=(2,1))
    def test_duplicate_subset(self):self.deny('BAD_SUBSET',subset=(1,1))
    def test_empty_subset(self):self.deny('BAD_SUBSET',subset=())
    def test_negative_subset(self):self.deny('BAD_SUBSET',subset=(-1,))
    def test_wrong_dataset_root(self):self.deny('MISSING_DATASET_ANCESTRY',roots=['else'])
    def test_no_roots(self):self.deny('BAD_ANCESTRY',roots=[])
    def test_duplicate_roots(self):self.deny('BAD_ANCESTRY',roots=['holdout-204','holdout-204'])
    def test_noncanonical_roots(self):self.deny('NONCANONICAL_ANCESTRY',roots=['up','holdout-204'])
    def test_unregistered_agent(self):self.deny('UNREGISTERED_AGENT',agent='rogue')
    def test_bad_credit_zero(self):self.deny('BAD_CREDITS',credits=0)
    def test_bad_credit_negative(self):self.deny('BAD_CREDITS',credits=-1)
    def test_bad_credit_float(self):self.deny('BAD_CREDITS',credits=1.5)
    def test_bad_credit_bool(self):self.deny('BAD_CREDITS',credits=True)
    def test_bad_id(self):self.deny('BAD_EVENT',ident='')
    def test_bad_recipient(self):self.deny('BAD_EVENT',recipient='')
    def test_bad_policy(self):
        with self.assertRaises(Reject):Policy('x',0,1,1,('a',))
    def test_bad_agents(self):
        with self.assertRaises(Reject):Policy('x',1,1,1,('a','a'))
    def test_audit_tamper(self):
        self.send();self.f.ledger.db.execute("UPDATE events SET body='{}'")
        with self.assertRaisesRegex(Reject,'CORRUPT_LOG'):self.f.audit()
    def test_head_tamper(self):
        self.send();self.f.ledger.db.execute("UPDATE events SET head='fake'")
        with self.assertRaisesRegex(Reject,'CORRUPT_LOG'):self.f.audit()
    def test_atomic_after_corruption(self):
        self.send();self.f.ledger.db.execute("UPDATE events SET previous='fake'")
        with self.assertRaisesRegex(Reject,'CORRUPT_LOG'):self.send('two')
        self.assertEqual(self.f.ledger.db.execute('SELECT COUNT(*) FROM events').fetchone()[0],1)
    def test_restart_replay(self):
        with tempfile.TemporaryDirectory() as td:
            path=os.path.join(td,'e.db');a=FLAY204(self.p,path);a.release('one','ada','c',[0],1,1);a.ledger.close()
            b=FLAY204(self.p,path)
            with self.assertRaisesRegex(Reject,'REPLAY'):b.release('one','ada','c',[0],1,1)
            self.assertEqual(b.audit()['events'],1)
    def test_restart_global_budget(self):
        with tempfile.TemporaryDirectory() as td:
            path=os.path.join(td,'e.db');a=FLAY204(self.p,path);a.release('one','ada','c',[0],8,1);a.ledger.close()
            b=FLAY204(self.p,path);b.release('two','bert','d',[1],4,2)
            with self.assertRaisesRegex(Reject,'GLOBAL_BUDGET_EXCEEDED'):b.release('three','clio','e',[2],1,3)
    def test_fixture(self):
        f=fixture();self.assertEqual(f['recipient_refusal'],'RECIPIENT_BUDGET_EXCEEDED');self.assertEqual(f['global_refusal'],'GLOBAL_BUDGET_EXCEEDED')
    def test_determinism(self):self.assertEqual(fixture(),fixture())
    def test_payload_hash(self):self.send(payload={'x':1});self.assertEqual(self.f.ledger.check_chain()[0][0]['payload_hash'],digest({'x':1}))
    def test_noncause_caveat(self):self.assertIn('No proof',self.f.audit()['caveat'])

if __name__ == '__main__':unittest.main()