import unittest, tempfile, os, copy
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from anchor import *
class TestAnchors(unittest.TestCase):
    def setUp(self):self.log,self.receipts,self.trust,self.keys=fixture()
    def test_match(self):self.assertEqual(audit(self.log,self.receipts,self.trust)['status'],'ANCHORED_MATCH')
    def test_extension(self):self.assertEqual(audit(make_log(9),self.receipts,self.trust)['status'],'VALID_EXTENSION')
    def test_truncation(self):self.assertEqual(audit(self.log[:4],self.receipts,self.trust)['status'],'CLEAN_SUFFIX_TRUNCATION')
    def test_no_receipts(self):self.assertEqual(audit(self.log,[],self.trust)['status'],'ANCHOR_UNAVAILABLE')
    def test_tamper_log(self):
        l=copy.deepcopy(self.log);l[0]['selected']='B';self.assertEqual(audit(l,self.receipts,self.trust)['status'],'LOCAL_LOG_TAMPERED')
    def test_modify_record_head(self):
        l=copy.deepcopy(self.log);l[4]['head']='a'*64;self.assertEqual(audit(l,self.receipts,self.trust)['status'],'LOCAL_LOG_TAMPERED')
    def test_reorder_records(self):self.assertEqual(audit(self.log[::-1],self.receipts,self.trust)['status'],'LOCAL_LOG_TAMPERED')
    def test_invalid_signature(self):
        r=copy.deepcopy(self.receipts);r[0]['signature']='00'*64;self.assertEqual(audit(self.log,r,self.trust)['status'],'UNTRUSTED_ANCHOR')
    def test_unknown_root(self):
        r=copy.deepcopy(self.receipts);r[0]['body']['root']='Z';self.assertEqual(audit(self.log,r,self.trust)['status'],'UNTRUSTED_ANCHOR')
    def test_signed_fork(self):
        r=copy.deepcopy(self.receipts);body={**r[0]['body'],'head':'a'*64,'nonce':'fork'};r.append(signed(self.keys['A'],body));self.assertEqual(audit(self.log,r,self.trust)['status'],'SIGNED_FORK')
    def test_admin_conflict(self):
        trust={n:Custodian(c.public_key,'one-admin') for n,c in self.trust.items()}
        receipts=[signed(self.keys[n],commitment(self.log,n,'one-admin',n)) for n in self.keys]
        self.assertEqual(audit(self.log,receipts,trust)['status'],'SHARED_ADMINISTRATION')
    def test_single_root(self):self.assertEqual(audit(self.log,self.receipts[:1],self.trust)['status'],'SHARED_ADMINISTRATION')
    def test_two_roots(self):self.assertTrue(audit(self.log,self.receipts[:2],self.trust)['accepted'])
    def test_real_independence_unverified(self):self.assertFalse(audit(self.log,self.receipts,self.trust)['independent_operators_verified'])
    def test_not_activate(self):self.assertFalse(audit(self.log,self.receipts,self.trust)['jane_activation'])
    def test_untrusted_receipt(self):self.assertEqual(audit(self.log,[{}],self.trust)['status'],'UNTRUSTED_ANCHOR')
    def test_invalid_log_type(self):self.assertFalse(verify_log(None))
    def test_invalid_log_sequence(self):
        l=copy.deepcopy(self.log);l[0]['sequence']=True;self.assertFalse(verify_log(l))
    def test_invalid_log_selected(self):
        l=copy.deepcopy(self.log);l[0]['selected']='X';self.assertFalse(verify_log(l))
    def test_empty_log(self):self.assertTrue(verify_log([]))
    def test_cannot_anchor_empty(self):
        with self.assertRaises(ValueError):commitment([],'A','admin-A','n')
    def test_signature(self):self.assertTrue(authentic(self.trust['A'].public_key,self.receipts[0]['body'],self.receipts[0]['signature']))
    def test_signature_tamper(self):self.assertFalse(authentic(self.trust['A'].public_key,{**self.receipts[0]['body'],'head':'x'*64},self.receipts[0]['signature']))
    def test_determinism(self):self.assertEqual(make_log(6),make_log(6))
    def test_canonical(self):self.assertEqual(canonical({'b':1,'a':2}),canonical({'a':2,'b':1}))
    def test_deterministic_anchors(self):self.assertEqual(self.receipts,fixture()[1])
    def test_store_retain(self):
        with tempfile.TemporaryDirectory() as d:
            a=AnchorStore(os.path.join(d,'external.sqlite'),self.trust)
            self.assertEqual(a.retain(self.receipts[0]),'RETAINED');self.assertEqual(len(a.receipts()),1);a.close()
    def test_store_restart(self):
        with tempfile.TemporaryDirectory() as d:
            p=os.path.join(d,'external.sqlite');a=AnchorStore(p,self.trust);a.retain(self.receipts[0]);a.close();a=AnchorStore(p,self.trust)
            self.assertEqual(a.retain(self.receipts[0]),'DUPLICATE');a.close()
    def test_store_bad_signature(self):
        with tempfile.TemporaryDirectory() as d:
            a=AnchorStore(':memory:',self.trust);r=copy.deepcopy(self.receipts[0]);r['signature']='ab'*64
            self.assertEqual(a.retain(r),'BAD_SIGNATURE');a.close()
    def test_store_signed_fork(self):
        a=AnchorStore(':memory:',self.trust);a.retain(self.receipts[0]);r=signed(self.keys['A'],{**self.receipts[0]['body'],'head':'f'*64,'nonce':'fork'})
        self.assertEqual(a.retain(r),'SIGNED_FORK');a.close()
    def test_store_stale_anchor(self):
        a=AnchorStore(':memory:',self.trust);a.retain(self.receipts[0]);r=signed(self.keys['A'],commitment(make_log(3),'A','admin-A','low'))
        self.assertEqual(a.retain(r),'STALE_ANCHOR');a.close()
    def test_store_newer_anchor(self):
        a=AnchorStore(':memory:',self.trust);a.retain(self.receipts[0]);r=signed(self.keys['A'],commitment(make_log(8),'A','admin-A','high'))
        self.assertEqual(a.retain(r),'RETAINED');a.close()
    def test_nonce_reuse(self):
        a=AnchorStore(':memory:',self.trust);a.retain(self.receipts[0]);r=signed(self.keys['A'],commitment(make_log(8),'A','admin-A','nonce-A'))
        self.assertEqual(a.retain(r),'REPLAY_NONCE');a.close()
    def test_distinct_store(self):
        with tempfile.TemporaryDirectory() as d:
            a=AnchorStore(os.path.join(d,'external.sqlite'),self.trust)
            for receipt in self.receipts:self.assertEqual(a.retain(receipt),'RETAINED')
            self.assertEqual(audit(self.log,a.receipts(),self.trust)['status'],'ANCHORED_MATCH');a.close()
    def test_reject_empty_id(self):
        with self.assertRaises(ValueError):commitment(self.log,'A','','x')
    def test_head_length(self):self.assertEqual(len(self.log[-1]['head']),64)
    def test_all_sequences(self):self.assertEqual([r['sequence'] for r in self.log],[1,2,3,4,5,6])
    def test_returned_empty_with_anchor(self):self.assertEqual(audit([],self.receipts,self.trust)['status'],'CLEAN_SUFFIX_TRUNCATION')
    def test_audit_prefix_anchor(self):
        r=[signed(self.keys['A'],commitment(make_log(3),'A','admin-A','early-A')),signed(self.keys['B'],commitment(make_log(3),'B','admin-B','early-B'))]
        self.assertEqual(audit(self.log,r,self.trust)['status'],'VALID_EXTENSION')
if __name__=='__main__':unittest.main(verbosity=2)
