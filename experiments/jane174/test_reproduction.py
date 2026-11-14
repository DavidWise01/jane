import os
import tempfile
import unittest
from copy import deepcopy
from reproduction import *

class Setup(unittest.TestCase):
    def setUp(self):
        self.priv={s:key(s+'-174') for s in 'ABC'}
        self.pub={s:p.public_key() for s,p in self.priv.items()}
        self.blobs={(s,s+'1'):('raw'+s).encode() for s in 'ABC'}
        self.receipts=[acquisition(s,s+'1','capture-v1',self.blobs[(s,s+'1')],1000+ord(s)-65,['root'+s],self.priv[s]) for s in 'ABC']
        self.policy=Policy('capture-v1',5)
    def f(self,p=None,ledger=None):return FLAY(self.pub,p or self.policy,ledger)
    def audit(self,receipts=None,blobs=None,policy=None):return self.f(policy).audit(receipts if receipts is not None else self.receipts,blobs if blobs is not None else self.blobs)
    def test_reproduced(self):self.assertEqual(self.audit()['status'],'REPRODUCED_DECLARED_FIXTURE')
    def test_three_valid(self):self.assertEqual(self.audit()['valid_acquisitions'],3)
    def test_support_three(self):self.assertEqual(len(self.audit()['declared_independent_support']),3)
    def test_no_physical_claim(self):self.assertFalse(self.audit()['physical_independence_verified'])
    def test_no_learning(self):self.assertFalse(self.audit()['learning_applied'])
    def test_parent_frozen(self):self.assertEqual(self.audit()['active'],'FROZEN_PARENT')
    def test_digest_stable(self):self.assertEqual(self.audit()['evidence_digest'],self.audit()['evidence_digest'])
    def test_scope(self):self.assertIn('fixtures',self.audit()['scope'])
    def test_insufficient(self):self.assertEqual(self.audit(self.receipts[:1])['status'],'INVALID_RECEIPT_COUNT')
    def test_missing_blob(self):
        b=dict(self.blobs);del b[('A','A1')]
        self.assertEqual(self.audit(blobs=b)['status'],'REPRODUCED_WITH_REJECTIONS')
    def test_tampered_raw(self):
        b=dict(self.blobs);b[('A','A1')]=b'forged'
        self.assertEqual(self.audit(blobs=b)['rejected'][0]['reason'],'RAW_COMMITMENT_MISMATCH')
    def test_signature_tamper(self):
        r=deepcopy(self.receipts);r[0]['payload']['value_milli']=333
        self.assertEqual(self.audit(r)['rejected'][0]['reason'],'BAD_SIGNATURE')
    def test_identity_mismatch(self):
        r=deepcopy(self.receipts);r[0]['signer']='B'
        self.assertEqual(self.audit(r)['rejected'][0]['reason'],'BAD_SIGNATURE')
    def test_bad_signature_hex(self):
        r=deepcopy(self.receipts);r[0]['signature']='nope'
        self.assertEqual(self.audit(r)['rejected'][0]['reason'],'BAD_SIGNATURE')
    def test_bad_procedure(self):
        r=deepcopy(self.receipts);r[0]=acquisition('A','A1','other',self.blobs[('A','A1')],1000,['rootA'],self.priv['A'])
        self.assertEqual(self.audit(r)['rejected'][0]['reason'],'PROCEDURE_MISMATCH')
    def test_bad_future(self):
        r=deepcopy(self.receipts);r[0]=acquisition('A','A1','capture-v1',self.blobs[('A','A1')],1000,['rootA'],self.priv['A'],1101)
        self.assertEqual(self.audit(r)['rejected'][0]['reason'],'STALE_OR_FUTURE')
    def test_expired(self):
        r=deepcopy(self.receipts);r[0]=acquisition('A','A1','capture-v1',self.blobs[('A','A1')],1000,['rootA'],self.priv['A'],799)
        self.assertEqual(self.audit(r)['rejected'][0]['reason'],'STALE_OR_FUTURE')
    def test_shared_root(self):
        r=deepcopy(self.receipts);r[1]=acquisition('B','B1','capture-v1',self.blobs[('B','B1')],1001,['rootA'],self.priv['B'])
        self.assertEqual(self.audit(r)['status'],'SHARED_ACQUISITION_ANCESTRY')
    def test_shared_parent_on_multiple(self):
        r=deepcopy(self.receipts);r[1]=acquisition('B','B1','capture-v1',self.blobs[('B','B1')],1001,['rootA','rootB'],self.priv['B'])
        self.assertEqual(self.audit(r)['status'],'SHARED_ACQUISITION_ANCESTRY')
    def test_diff_values(self):
        r=deepcopy(self.receipts);r[1]=acquisition('B','B1','capture-v1',self.blobs[('B','B1')],1100,['rootB'],self.priv['B'])
        self.assertEqual(self.audit(r)['status'],'MEASUREMENT_DISAGREEMENT')
    def test_edge_tolerance(self):
        r=deepcopy(self.receipts);r[1]=acquisition('B','B1','capture-v1',self.blobs[('B','B1')],1005,['rootB'],self.priv['B'])
        self.assertEqual(self.audit(r)['status'],'REPRODUCED_DECLARED_FIXTURE')
    def test_over_tolerance(self):
        r=deepcopy(self.receipts);r[1]=acquisition('B','B1','capture-v1',self.blobs[('B','B1')],1006,['rootB'],self.priv['B'])
        self.assertEqual(self.audit(r)['status'],'MEASUREMENT_DISAGREEMENT')
    def test_duplicate_run(self):
        r=[self.receipts[0],self.receipts[0],self.receipts[1]]
        self.assertEqual(self.audit(r)['rejected'][0]['reason'],'DUPLICATE_RUN')
    def test_persistent_replay(self):
        with tempfile.TemporaryDirectory() as td:
            path=os.path.join(td,'journal.db')
            self.f(ledger=Ledger(path)).audit(self.receipts,self.blobs)
            out=self.f(ledger=Ledger(path)).audit(self.receipts,self.blobs)
            self.assertEqual(out['status'],'NO_VALID_ACQUISITIONS')
            self.assertEqual(len(out['rejected']),3)
    def test_invalid_ancestry_empty(self):
        r=deepcopy(self.receipts);r[0]=acquisition('A','A1','capture-v1',self.blobs[('A','A1')],1000,[],self.priv['A'])
        self.assertEqual(self.audit(r)['rejected'][0]['reason'],'INVALID_ANCESTRY')
    def test_invalid_ancestry_duplicates(self):
        r=deepcopy(self.receipts);r[0]=acquisition('A','A1','capture-v1',self.blobs[('A','A1')],1000,['x','x'],self.priv['A'])
        self.assertEqual(self.audit(r)['rejected'][0]['reason'],'INVALID_ANCESTRY')
    def test_invalid_noninteger_value(self):
        r=deepcopy(self.receipts);r[0]=acquisition('A','A1','capture-v1',self.blobs[('A','A1')],True,['rootA'],self.priv['A'])
        self.assertEqual(self.audit(r)['rejected'][0]['reason'],'INVALID_VALUE')
    def test_policy_bad_tolerance(self):
        with self.assertRaises(ValueError):Policy('x',-1)
    def test_policy_bad_roots(self):
        with self.assertRaises(ValueError):Policy('x',required_roots=1)
    def test_policy_bad_receipt_budget(self):
        with self.assertRaises(ValueError):Policy('x',max_receipts=1)
    def test_policy_blank_procedure(self):
        with self.assertRaises(ValueError):Policy('')
    def test_policy_no_bool(self):
        with self.assertRaises(ValueError):Policy('x',True)
    def test_policy_limit_receipts(self):self.assertEqual(self.audit(policy=Policy('capture-v1',max_receipts=2))['status'],'INVALID_RECEIPT_COUNT')
    def test_ledger_check(self):
        f=self.f();f.audit(self.receipts,self.blobs);self.assertEqual(f.ledger.check(),'VALID_LOCAL_CHAIN')
    def test_ledger_external(self):
        f=self.f();f.audit(self.receipts,self.blobs);self.assertEqual(f.ledger.check('a'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_ledger_tamper(self):
        f=self.f();f.audit(self.receipts,self.blobs)
        f.ledger.db.execute("update events set kind='ALTERED' where seq=0")
        self.assertEqual(f.ledger.check(),'JOURNAL_TAMPERED')
    def test_ledger_restart(self):
        with tempfile.TemporaryDirectory() as td:
            path=os.path.join(td,'l.db');f=self.f(ledger=Ledger(path));f.audit(self.receipts,self.blobs)
            self.assertEqual(Ledger(path).check(),'VALID_LOCAL_CHAIN')
    def test_sha_value(self):self.assertEqual(len(digest(b'raw')),64)
    def test_signature_verify(self):self.assertTrue(verify(self.receipts[0],self.pub))
    def test_signature_reject(self):self.assertFalse(verify({'signer':'Z','payload':{},'signature':'00'},self.pub))
    def test_deterministic_example(self):self.assertEqual(example()['result']['status'],'REPRODUCED_DECLARED_FIXTURE')
    def test_example_ledger(self):self.assertEqual(example()['ledger_check'],'VALID_LOCAL_CHAIN')
    def test_subset_two(self):self.assertEqual(self.audit(self.receipts[:2])['status'],'REPRODUCED_DECLARED_FIXTURE')
    def test_threshold_three(self):self.assertEqual(self.audit(self.receipts[:2],policy=Policy('capture-v1',required_roots=3))['status'],'INSUFFICIENT_VALID_ACQUISITIONS')
    def test_one_reject_below_quorum(self):
        b=dict(self.blobs);del b[('A','A1')]
        self.assertEqual(self.audit(blobs=b,policy=Policy('capture-v1',required_roots=3))['status'],'INSUFFICIENT_VALID_ACQUISITIONS')
if __name__=='__main__':unittest.main(verbosity=2)