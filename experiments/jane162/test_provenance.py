import unittest
import tempfile
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from provenance import *

class TestProvenance(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'test.db'
        self.signer=SchedulerSigner(Ed25519PrivateKey.from_private_bytes(bytes(range(32))))
        self.audit=FLAYObserverAudit(self.path,self.signer.public_key())
    def tearDown(self):self.audit.close();self.temp.cleanup()
    def emit(self,selected='A',enabled=('A','B'),tick=None):
        return self.signer.issue(self.signer.seq if tick is None else tick,enabled,selected)
    def test_01_valid_capture(self):self.assertEqual(self.audit.capture(self.emit()),'ACCEPTED')
    def test_02_signature(self):self.assertEqual(verify_receipt(self.emit(),self.signer.public_key(),'hive-a','epoch-1'),'VALID_SIGNATURE')
    def test_03_modification(self):
        r=self.emit();r['decision']['selected']='B';self.assertEqual(self.audit.capture(r),'BAD_SIGNATURE')
    def test_04_foreign_key(self):self.assertEqual(verify_receipt(self.emit(),Ed25519PrivateKey.generate().public_key(),'hive-a','epoch-1'),'BAD_SIGNATURE')
    def test_05_foreign_scheduler(self):self.assertEqual(verify_receipt(self.emit(),self.signer.public_key(),'other','epoch-1'),'FOREIGN_IDENTITY')
    def test_06_foreign_epoch(self):self.assertEqual(verify_receipt(self.emit(),self.signer.public_key(),'hive-a','epoch-2'),'FOREIGN_IDENTITY')
    def test_07_bad_selected(self):
        with self.assertRaises(ValueError):self.emit('C')
    def test_08_bad_tick(self):
        with self.assertRaises(ValueError):self.emit(tick=-1)
    def test_09_replay(self):
        r=self.emit();self.audit.capture(r);self.assertEqual(self.audit.capture(r),'REPLAY')
    def test_10_restart_replay(self):
        r=self.emit();self.audit.capture(r);self.audit.close();self.audit=FLAYObserverAudit(self.path,self.signer.public_key());self.assertEqual(self.audit.capture(r),'REPLAY')
    def test_11_signed_equivocation(self):
        r=self.emit();self.audit.capture(r)
        duplicate=dict(decision={**r['decision'],'selected':'B'})
        duplicate['signature']=self.signer.key.sign(canonical(duplicate['decision'])).hex()
        self.assertEqual(self.audit.capture(duplicate),'SIGNED_EQUIVOCATION')
    def test_12_missing_prefix(self):
        self.emit();self.assertEqual(self.audit.capture(self.emit()),'MISSING_PREFIX')
    def test_13_missing_sequence(self):
        self.audit.capture(self.emit());self.emit();self.assertEqual(self.audit.capture(self.emit()),'MISSING_SEQUENCE')
    def test_14_broken_chain(self):
        self.audit.capture(self.emit());r=self.emit();r['decision']['prev']='f'*64;r['signature']=self.signer.key.sign(canonical(r['decision'])).hex();self.assertEqual(self.audit.capture(r),'BROKEN_SIGNED_CHAIN')
    def test_15_nonmonotonic_tick(self):
        self.audit.capture(self.emit(tick=1));self.assertEqual(self.audit.capture(self.emit(tick=1)),'NONMONOTONIC_TICK')
    def test_16_valid_chain(self):
        self.assertEqual([self.audit.capture(self.emit()) for _ in range(3)],['ACCEPTED']*3)
    def test_17_observer_match(self):
        r=self.emit();d=r['decision'];self.assertEqual(self.audit.capture(r,{'seq':0,'tick':0,'enabled':d['enabled'],'selected':'A'}),'ACCEPTED')
    def test_18_observer_lie(self):
        r=self.emit();self.assertEqual(self.audit.capture(r,{'seq':0,'tick':0,'enabled':['A','B'],'selected':'B'}),'OBSERVER_CONTRADICTION')
    def test_19_observer_lie_still_keeps_receipt(self):
        r=self.emit();self.audit.capture(r,{'seq':0,'tick':0,'enabled':['A','B'],'selected':'B'});self.assertEqual(self.audit.capture(r),'REPLAY')
    def test_20_invalid_report(self):self.assertEqual(self.audit.capture(self.emit(),['bad']),'INVALID_REPORT')
    def test_21_missing_observer(self):
        r=self.emit();self.audit.capture(r);x=self.audit.reconcile_observer_window([],0,0);self.assertEqual(x['status'],'OBSERVER_OMISSION')
    def test_22_missing_source(self):self.assertEqual(self.audit.reconcile_observer_window([],0,0)['status'],'MISSING_SIGNED_SOURCE')
    def test_23_window_matches(self):
        reports=[]
        for i in range(3):
            r=self.emit();self.audit.capture(r);reports.append(r['decision'])
        self.assertEqual(self.audit.reconcile_observer_window(reports,0,2)['status'],'MATCHED_WINDOW')
    def test_24_window_contradiction(self):
        r=self.emit();self.audit.capture(r);rep=dict(r['decision'],selected='B');self.assertEqual(self.audit.reconcile_observer_window([rep],0,0)['status'],'OBSERVER_CONTRADICTION')
    def test_25_duplicate_reports(self):
        r=self.emit();self.audit.capture(r);self.assertEqual(self.audit.reconcile_observer_window([r['decision'],r['decision']],0,0)['status'],'OBSERVER_DUPLICATES')
    def test_26_missing_middle_report(self):
        rs=[self.emit() for _ in range(3)]
        for r in rs:self.audit.capture(r)
        self.assertEqual(self.audit.reconcile_observer_window([rs[0]['decision'],rs[2]['decision']],0,2)['missing_observer'],[1])
    def test_27_missing_middle_source(self):
        a=self.emit();self.audit.capture(a);self.emit();c=self.emit();self.audit.capture(c)
        self.assertEqual(self.audit.reconcile_observer_window([a['decision'],c['decision']],0,2)['missing_source'],[1,2])
    def test_28_ledger(self):self.audit.capture(self.emit());self.assertEqual(self.audit.check_ledger(),'VALID_LOCAL_CHAIN')
    def test_29_tamper_ledger(self):
        self.audit.capture(self.emit());self.audit.db.execute("UPDATE events SET kind='FORGED'");self.audit.db.commit();self.assertEqual(self.audit.check_ledger(),'TAMPERED_LEDGER')
    def test_30_external_head(self):
        self.audit.capture(self.emit());self.assertEqual(self.audit.check_ledger('f'*64),'HEAD_MISMATCH')
    def test_31_anchor_on_open(self):
        self.audit.close();self.audit=FLAYObserverAudit(self.path,self.signer.public_key(),expected_head='f'*64);self.assertEqual(self.audit.external_anchor_status,'HEAD_MISMATCH')
    def test_32_anchor_not_provided(self):self.assertEqual(self.audit.external_anchor_status,'NOT_PROVIDED')
    def test_33_zero_initial_head(self):self.assertEqual(self.audit.head(),GENESIS)
    def test_34_restart_ledger(self):
        self.audit.capture(self.emit());head=self.audit.head();self.audit.close();self.audit=FLAYObserverAudit(self.path,self.signer.public_key(),expected_head=head);self.assertEqual(self.audit.check_ledger(head),'VALID_LOCAL_CHAIN')
    def test_35_bound_window(self):
        with self.assertRaises(ValueError):self.audit.reconcile_observer_window([],0,10001)
    def test_36_inverted_window(self):
        with self.assertRaises(ValueError):self.audit.reconcile_observer_window([],2,1)
    def test_37_negative_window(self):
        with self.assertRaises(ValueError):self.audit.reconcile_observer_window([],-1,0)
    def test_38_invalid_report_seq(self):
        with self.assertRaises(ValueError):self.audit.reconcile_observer_window([{'seq':True}],0,0)
    def test_39_receipt_missing_fields(self):self.assertEqual(self.audit.capture({'decision':{},'signature':'f'}),'MALFORMED')
    def test_40_receipt_wrong_signature(self):
        r=self.emit();r['signature']='00';self.assertEqual(self.audit.capture(r),'BAD_SIGNATURE')
    def test_41_enable_dedupe(self):self.assertEqual(self.emit(enabled=('B','A','B'))['decision']['enabled'],['A','B'])
    def test_42_demo_omission(self):self.assertEqual(demo()['reconciliation']['status'],'OBSERVER_OMISSION')
    def test_43_demo_no_independence(self):self.assertEqual(demo()['independent_witness_increment'],0)
    def test_44_demo_no_activation(self):self.assertFalse(demo()['reconciliation']['jane_approval'])
    def test_45_demo_valid_ledger(self):self.assertEqual(demo()['ledger_audit'],'VALID_LOCAL_CHAIN')
if __name__=='__main__':unittest.main(verbosity=2)