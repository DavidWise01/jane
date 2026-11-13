import copy
from datetime import timedelta
from pathlib import Path
import tempfile
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from portable import (
    Trust,Verifier,fixture,demo,make_bundle,canon,pub,parse_chronos,TIME,
)

class PortableTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name)/"verify.sqlite")
        self.trust,self.anchors,self.bundle,self.endpoint,self.challenge,self.now = fixture()
        self.v = Verifier(self.path,self.trust,self.anchors,self.now)
    def tearDown(self):
        self.v.db.close()
        self.temp.cleanup()
    def test_valid_bundle(self):self.assertEqual(self.v.verify(self.bundle,self.endpoint,self.challenge),"VERIFIED_PORTABLE_FIXTURE")
    def test_demo(self):self.assertEqual(demo()["first"],"VERIFIED_PORTABLE_FIXTURE")
    def test_replay(self):
        self.v.verify(self.bundle,self.endpoint,self.challenge)
        self.assertEqual(self.v.verify(self.bundle,self.endpoint,self.challenge),"REPLAY")
    def test_persistent_replay(self):
        self.v.verify(self.bundle,self.endpoint,self.challenge)
        self.v.db.close();self.v=Verifier(self.path,self.trust,self.anchors,self.now)
        self.assertEqual(self.v.verify(self.bundle,self.endpoint,self.challenge),"REPLAY")
    def test_changed_head(self):
        b=copy.deepcopy(self.bundle);b['statement']['checkpoint_head']='0'*64
        self.assertEqual(self.v.verify(b,self.endpoint,self.challenge),"INVALID_PROOF")
    def test_changed_chronos(self):
        b=copy.deepcopy(self.bundle);b['statement']['chronos']=b['statement']['chronos'].replace('19.32.00','19.33.00')
        self.assertEqual(self.v.verify(b,self.endpoint,self.challenge),"INVALID_PROOF")
    def test_wrong_endpoint(self):self.assertEqual(self.v.verify(self.bundle,"https://different.example.invalid",self.challenge),"BINDING_MISMATCH")
    def test_wrong_challenge(self):self.assertEqual(self.v.verify(self.bundle,self.endpoint,"other-challenge-00001"),"BINDING_MISMATCH")
    def test_short_challenge(self):self.assertEqual(self.v.verify(self.bundle,self.endpoint,"short"),"BINDING_MISMATCH")
    def test_missing_operator(self):
        self.v.trust=Trust(self.trust.attestors,{})
        self.assertEqual(self.v.verify(self.bundle,self.endpoint,self.challenge),"UNKNOWN_OPERATOR")
    def test_changed_root_registry(self):
        ops=dict(self.trust.operators);key,root,endpoint=ops['operator-A'];ops['operator-A']=(key,'different',endpoint)
        self.v.trust=Trust(self.trust.attestors,ops)
        self.assertEqual(self.v.verify(self.bundle,self.endpoint,self.challenge),"IDENTITY_MISMATCH")
    def test_missing_attestors(self):
        b=copy.deepcopy(self.bundle);b['attestations']=[]
        self.assertEqual(self.v.verify(b,self.endpoint,self.challenge),"ATTESTATION_INSUFFICIENT")
    def test_duplicate_attestor(self):
        b=copy.deepcopy(self.bundle);b['attestations']=[b['attestations'][0]]*2
        self.assertEqual(self.v.verify(b,self.endpoint,self.challenge),"ATTESTATION_INSUFFICIENT")
    def test_shared_attestor_control(self):
        a=dict(self.trust.attestors);a['att-1']=(a['att-1'][0],a['att-0'][1]);self.v.trust=Trust(a,self.trust.operators)
        self.assertEqual(self.v.verify(self.bundle,self.endpoint,self.challenge),"ATTESTATION_INSUFFICIENT")
    def test_same_control_as_operator(self):
        a=dict(self.trust.attestors);a['att-1']=(a['att-1'][0],'fixture:operator-A');self.v.trust=Trust(a,self.trust.operators)
        self.assertEqual(self.v.verify(self.bundle,self.endpoint,self.challenge),"ATTESTATION_INSUFFICIENT")
    def test_unknown_attestor(self):
        b=copy.deepcopy(self.bundle);b['attestations'][1]['attestor_id']='unknown'
        self.assertEqual(self.v.verify(b,self.endpoint,self.challenge),"ATTESTATION_INSUFFICIENT")
    def test_bad_attestation_signature(self):
        b=copy.deepcopy(self.bundle);b['attestations'][0]['signature']=b['attestations'][1]['signature']
        self.assertEqual(self.v.verify(b,self.endpoint,self.challenge),"INVALID_PROOF")
    def test_no_anchor(self):
        self.v.anchors={}
        self.assertEqual(self.v.verify(self.bundle,self.endpoint,self.challenge),"ANCHOR_UNAVAILABLE")
    def test_anchor_rollback(self):
        root='fixture:operator-A';self.v.anchors={root:(9,'f'*64)}
        self.assertEqual(self.v.verify(self.bundle,self.endpoint,self.challenge),"CHECKPOINT_ROLLBACK")
    def test_anchor_fork(self):
        root='fixture:operator-A';self.v.anchors={root:(8,'f'*64)}
        self.assertEqual(self.v.verify(self.bundle,self.endpoint,self.challenge),"CHECKPOINT_FORK")
    def test_pinned_fork(self):
        s=self.bundle['statement'];self.v.db.execute('INSERT INTO checked VALUES(?,?,?)',(s['custody_root'],s['checkpoint_sequence'],'f'*64));self.v.db.commit()
        self.assertEqual(self.v.verify(self.bundle,self.endpoint,self.challenge),"EQUIVOCATION")
    def test_stale(self):
        self.v.now+=timedelta(hours=1)
        self.assertEqual(self.v.verify(self.bundle,self.endpoint,self.challenge),"STALE_CHRONOS")
    def test_invalid_calendar(self):
        with self.assertRaises(ValueError):parse_chronos('{{ 2026.02.30 }}{{ 19.32.00 }}{{ 123.45.56 }}',-360)
    def test_invalid_angle(self):
        with self.assertRaises(ValueError):parse_chronos('{{ 2026.11.12 }}{{ 19.32.00 }}{{ 123.60.56 }}',-360)
    def test_invalid_offset(self):
        with self.assertRaises(ValueError):parse_chronos(TIME,900)
    def test_invalid_schema(self):
        b=copy.deepcopy(self.bundle);b['statement']['extra']='scout instruction'
        self.assertEqual(self.v.verify(b,self.endpoint,self.challenge),"INVALID_SCHEMA")
    def test_false_is_not_sequence(self):
        b=copy.deepcopy(self.bundle);b['statement']['checkpoint_sequence']=False
        self.assertEqual(self.v.verify(b,self.endpoint,self.challenge),"INVALID_SCHEMA")
    def test_event_chain(self):
        self.v.verify(self.bundle,self.endpoint,self.challenge)
        self.assertEqual(self.v.audit(),"VALID_LOCAL_EVENT_CHAIN")
    def test_event_tamper(self):
        self.v.verify(self.bundle,self.endpoint,self.challenge);self.v.events[0]['status']='rewritten'
        self.assertEqual(self.v.audit(),"TAMPERED")
    def test_no_learning(self):self.assertFalse(demo()['learning_applied'])
    def test_no_actual_services(self):self.assertFalse(demo()['independent_witness_service_deployed'])
    def test_deterministic_classes(self):self.assertEqual(len(self.trust.operators),1)
    def test_bad_signature_b64(self):
        b=copy.deepcopy(self.bundle);b['operator_signature']='!invalid'
        self.assertEqual(self.v.verify(b,self.endpoint,self.challenge),"INVALID_PROOF")
    def test_bounded_attestor_count(self):
        with self.assertRaises(ValueError):Verifier(':memory:',self.trust,self.anchors,self.now,required_attestors=6)
    def test_empty_proof(self):self.assertEqual(self.v.verify({},self.endpoint,self.challenge),"INVALID_PROOF")
    def test_changed_statement_endpoint(self):
        b=copy.deepcopy(self.bundle);b['statement']['endpoint']='https://evil.invalid'
        self.assertEqual(self.v.verify(b,self.endpoint,self.challenge),"BINDING_MISMATCH")

if __name__ == '__main__':unittest.main(verbosity=2)