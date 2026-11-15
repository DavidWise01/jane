import unittest, tempfile, os
from dataclasses import replace
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from lineage import *

class TestJANE212(unittest.TestCase):
    def setUp(self):
        self.v,self.p,self.r,self.w,self.report=fixture()
    def tearDown(self):
        self.v.audit.close()
    def audit(self): return self.v.check(self.p,self.r,self.w,self.report)
    def test_complete(self): self.assertEqual(self.audit()['verdict'],'DECLARED_SEARCH_CONSISTENT_FIXTURE')
    def test_omission(self):
        v,p,r,w,x=fixture('omitted');self.assertEqual(v.check(p,r,w,x)['verdict'],'EXECUTED_QUERY_OMITTED_FROM_REPORT');v.audit.close()
    def test_unplanned(self):
        v,p,r,w,x=fixture('unplanned');self.assertEqual(v.check(p,r,w,x)['verdict'],'EXECUTION_OUTSIDE_COMMITTED_PLAN');v.audit.close()
    def test_missing(self):
        v,p,r,w,x=fixture('missing');self.assertEqual(v.check(p,r,w,x)['verdict'],'PLANNED_EXECUTION_MISSING');v.audit.close()
    def test_altered(self):
        v,p,r,w,x=fixture('altered');self.assertEqual(v.check(p,r,w,x)['verdict'],'REPORTED_RESULT_INCONSISTENT');v.audit.close()
    def test_replay(self):
        self.audit();self.assertEqual(self.audit()['verdict'],'REPLAY')
    def test_bad_plan_signature(self):
        self.p['payload']['frozen']=False
        self.assertEqual(self.audit()['verdict'],'INVALID_PLAN_SIGNATURE')
    def test_bad_executor_signature(self):
        self.r['payload']['count']=88
        self.assertEqual(self.audit()['verdict'],'INVALID_EXECUTION_SIGNATURE')
    def test_bad_witness_signature(self):
        self.w[0]['attestation']['signature']='00'
        self.assertEqual(self.audit()['verdict'],'INVALID_WITNESS')
    def test_shared_roots(self):
        self.w[1]=self.w[0].copy()
        self.assertEqual(self.audit()['verdict'],'SHARED_WITNESS_ANCESTRY')
    def test_insufficient_witnesses(self):
        self.assertEqual(self.v.check(self.p,self.r,[],self.report)['verdict'],'INSUFFICIENT_WITNESSES')
    def test_conflicting_witness_head(self):
        k=Ed25519PrivateKey.generate()
        self.v.witness_keys['beta']=k.public_key()
        self.w[1]['attestation']=seal(k,{'nonce':self.p['payload']['nonce'], 'plan_hash':digest(self.p['payload']), 'execution_count':3,'execution_head':'0'*64})
        self.assertEqual(self.audit()['verdict'],'WITNESS_HEAD_CONFLICT')
    def test_wrong_plan_hash(self):
        k=Ed25519PrivateKey.generate();self.v.execution_key=k.public_key()
        self.r=seal(k,dict(self.r['payload'],plan_hash='0'*64))
        self.assertEqual(self.audit()['verdict'],'EXECUTION_PLAN_MISMATCH')
    def test_wrong_execution_head(self):
        k=Ed25519PrivateKey.generate();self.v.execution_key=k.public_key()
        self.r=seal(k,dict(self.r['payload'],head='0'*64))
        self.assertEqual(self.audit()['verdict'],'EXECUTION_HEAD_MISMATCH')
    def test_invalid_query_plan(self):
        k=Ed25519PrivateKey.generate();self.v.plan_key=k.public_key()
        self.p=seal(k,dict(self.p['payload'],queries=['a','a']))
        self.assertEqual(self.audit()['verdict'],'INVALID_PLAN')
    def test_commitment_mismatch(self):
        k=Ed25519PrivateKey.generate();self.v.plan_key=k.public_key()
        self.p=seal(k,dict(self.p['payload'],query_commitment='f'*64))
        self.assertEqual(self.audit()['verdict'],'PLAN_COMMITMENT_MISMATCH')
    def test_nonce_invalid(self):
        k=Ed25519PrivateKey.generate();self.v.plan_key=k.public_key()
        self.p=seal(k,dict(self.p['payload'],nonce='x'))
        self.assertEqual(self.audit()['verdict'],'INVALID_NONCE')
    def test_different_reports_do_not_change_committed_data(self):
        original=digest(self.r['payload']);self.report.pop();self.audit();self.assertEqual(digest(self.r['payload']),original)
    def test_permutation_report_is_valid(self):
        self.report.reverse();self.assertEqual(self.audit()['verdict'],'DECLARED_SEARCH_CONSISTENT_FIXTURE')
    def test_empty_report(self):
        self.report=[];self.assertEqual(self.audit()['verdict'],'EXECUTED_QUERY_OMITTED_FROM_REPORT')
    def test_duplicate_report(self):
        self.report.append(self.report[0]);self.assertEqual(self.audit()['verdict'],'DUPLICATE_REPORT_ID')
    def test_invalid_report_shape(self):
        self.report=[{'id':1}];self.assertEqual(self.audit()['verdict'],'INVALID_REPORT')
    def test_audit_tamper(self):
        self.audit();self.v.audit.conn.execute("UPDATE verdicts SET verdict='CHANGED'");self.v.audit.conn.commit()
        self.assertEqual(self.audit()['verdict'],'CORRUPT_AUDIT')
    def test_replay_after_sqlite_restart(self):
        with tempfile.TemporaryDirectory() as t:
            db=os.path.join(t,'audit.db')
            self.v.audit.close();self.v.audit=Audit(db)
            self.audit();self.v.audit.close();self.v.audit=Audit(db)
            self.assertEqual(self.audit()['verdict'],'REPLAY')
    def test_distinct_nonce_valid(self):
        v,p,r,w,x=fixture(nonce='jane212-demo-0002');self.assertEqual(v.check(p,r,w,x)['verdict'],'DECLARED_SEARCH_CONSISTENT_FIXTURE');v.audit.close()
    def test_sha_determinism(self): self.assertEqual(digest({'a':1,'b':2}),digest({'b':2,'a':1}))
    def test_chain_order_sensitive(self): self.assertNotEqual(chain([{'id':1},{'id':2}])[-1],chain([{'id':2},{'id':1}])[-1])
    def test_signature_strict_shape(self): self.assertFalse(authenticate({'payload':{}},self.v.plan_key))
    def test_signature_invalid_hex(self): self.assertFalse(authenticate({'payload':{},'signature':'bad'},self.v.plan_key))
    def test_signature_wrong_key(self): self.assertFalse(authenticate(self.p,Ed25519PrivateKey.generate().public_key()))
    def test_witness_unknown_root(self):
        self.w[0]['root']='unknown';self.assertEqual(self.audit()['verdict'],'INVALID_WITNESS')
    def test_audit_clean_initially(self): self.assertTrue(self.v.audit.verify())
    def test_no_secret_reported(self): self.assertNotIn('private_key',str(self.audit()))

if __name__=='__main__': unittest.main()