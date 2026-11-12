import unittest
from dataclasses import replace
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from custody import *

def raw(k):return k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)

class CustodyTests(unittest.TestCase):
    def setUp(self):
        self.keys=[Ed25519PrivateKey.generate() for _ in range(3)]
        self.roots=['owned:canonical','external:A','external:B']
        self.admins=['own','A','B']
        self.identity={str(i):Identity(str(i),raw(k),self.roots[i],self.admins[i]) for i,k in enumerate(self.keys)}
        self.head='a'*64
        self.g=Gate(self.identity,{},chronos_utc(STAMP,-360))
    def receipt(self,i=0,head=None,nonce=None,seq=7,stamp=STAMP):
        p=dict(protocol='JANE-145',key_id=str(i),root=self.roots[i],sequence=seq,
               head=head or self.head,nonce=nonce or f'unique-nonce-{i}-long',chronos=stamp,utc_offset=-360)
        return Receipt(p,self.keys[i].sign(canonical(p)))
    def all_three(self):
        for i in range(3):self.assertEqual(self.g.receive(self.receipt(i)),'ACCEPTED')
    def test_demo_rollback(self):self.assertEqual(demo()[1]['status'],'ROLLBACK_DETECTED')
    def test_fixture_flag(self):self.assertFalse(demo()[1]['independent_operators_verified'])
    def test_good_signature(self):self.assertEqual(self.g.receive(self.receipt()),'ACCEPTED')
    def test_replay(self):
        r=self.receipt();self.g.receive(r);self.assertEqual(self.g.receive(r),'REPLAY')
    def test_tamper(self):
        r=self.receipt();p=dict(r.payload,head='b'*64)
        self.assertEqual(self.g.receive(Receipt(p,r.signature)),'BAD_SIGNATURE')
    def test_clock_tamper(self):
        r=self.receipt();p=dict(r.payload,chronos=r.payload['chronos'].replace('14.30','14.31'))
        self.assertEqual(self.g.receive(Receipt(p,r.signature)),'BAD_SIGNATURE')
    def test_stale(self):
        self.g.now += timedelta(hours=1)
        self.assertEqual(self.g.receive(self.receipt()),'STALE')
    def test_key_disabled(self):
        self.g.identities['0']=replace(self.identity['0'],enabled=False)
        self.assertEqual(self.g.receive(self.receipt()),'UNKNOWN_KEY')
    def test_missing(self):
        self.g.receive(self.receipt());self.assertEqual(self.g.assess(7,self.head)['status'],'INSUFFICIENT_CUSTODY')
    def test_match(self):
        self.all_three();self.assertEqual(self.g.assess(7,self.head)['status'],'MATCHED_FIXTURE_QUORUM')
    def test_rollback(self):
        self.all_three();self.assertEqual(self.g.assess(6,'b'*64)['status'],'ROLLBACK_DETECTED')
    def test_fork(self):
        self.all_three();self.assertEqual(self.g.assess(7,'b'*64)['status'],'FORK_DETECTED')
    def test_local_ahead(self):
        self.all_three();self.assertEqual(self.g.assess(8,'b'*64)['status'],'LOCAL_AHEAD')
    def test_cross_root_conflict(self):
        self.g.receive(self.receipt(0));self.g.receive(self.receipt(1,head='b'*64))
        self.assertEqual(self.g.assess(7,self.head)['status'],'CROSS_ROOT_CONFLICT')
    def test_equivocation(self):
        self.g.receive(self.receipt(0));self.g.receive(self.receipt(0,head='b'*64,nonce='second-nonce-long'))
        self.assertEqual(self.g.assess(7,self.head)['status'],'EQUIVOCATION_QUARANTINE')
    def test_equivocation_preserved(self):
        self.g.receive(self.receipt(0));self.g.receive(self.receipt(0,head='b'*64,nonce='second-nonce-long'))
        self.assertEqual(len(self.g.assess(7,self.head)['equivocations']),1)
    def test_same_admin_twice(self):
        self.g.identities['1']=replace(self.g.identities['1'],administrator='own')
        self.all_three();self.assertEqual(self.g.assess(7,self.head)['matching_administrators'],2)
    def test_same_admin_no_quorum(self):
        for i in range(3):self.g.identities[str(i)]=replace(self.g.identities[str(i)],administrator='one')
        self.all_three();self.assertEqual(self.g.assess(7,self.head)['status'],'INSUFFICIENT_CUSTODY')
    def test_mirror_same_root_no_quorum(self):
        self.g.identities['1']=replace(self.g.identities['1'],root='owned:canonical')
        p=self.receipt(1);p.payload['root']='owned:canonical';p=Receipt(p.payload,self.keys[1].sign(canonical(p.payload)))
        self.assertEqual(self.g.receive(p),'ACCEPTED')
        self.assertEqual(self.g.receive(self.receipt(0)),'ACCEPTED')
        self.assertEqual(self.g.assess(7,self.head)['status'],'CUSTODY_IDENTITY_CONFLICT')
    def test_key_rotation_cannot_change_admin_under_root(self):
        self.g.identities['1']=replace(self.g.identities['1'],root='owned:canonical',administrator='hijacked')
        p=self.receipt(1);p.payload['root']='owned:canonical';p=Receipt(p.payload,self.keys[1].sign(canonical(p.payload)))
        self.g.receive(p);self.g.receive(self.receipt(0))
        self.assertEqual(self.g.assess(7,self.head)['status'],'CUSTODY_IDENTITY_CONFLICT')
    def test_bad_offset(self):
        with self.assertRaises(ValueError):chronos_utc(STAMP,900)
    def test_invalid_angle(self):
        with self.assertRaises(ValueError):chronos_utc(STAMP.replace('123.45.56','123.65.56'),-360)
    def test_bad_date(self):
        with self.assertRaises(ValueError):chronos_utc(STAMP.replace('11.12','02.30'),-360)
    def test_audit(self):
        self.g.receive(self.receipt());self.assertEqual(self.g.audit(),'VALID_LOCAL_CHAIN')
    def test_audit_tamper(self):
        self.g.receive(self.receipt());self.g.events[0]['kind']='altered';self.assertEqual(self.g.audit(),'TAMPERED')
    def test_external_head(self):self.assertEqual(self.g.audit('b'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_no_learning(self):self.assertFalse(demo()[1]['learning_applied'])
    def test_deterministic_evaluation(self):
        self.all_three();self.assertEqual(self.g.assess(7,self.head)['status'],'MATCHED_FIXTURE_QUORUM')
    def test_no_fake_roots(self):
        self.assertEqual(len({i.root for i in self.identity.values()}),3)
    def test_bad_sequence(self):
        r=self.receipt();p=dict(r.payload,sequence=True)
        self.assertEqual(self.g.receive(Receipt(p,self.keys[0].sign(canonical(p)))),'BAD_CLAIM')
    def test_unsigned_spoof(self):
        r=self.receipt(0);p=dict(r.payload,key_id='1')
        self.assertEqual(self.g.receive(Receipt(p,r.signature)),'BAD_SIGNATURE')
    def test_conflicting_admin_claim_not_proof(self):
        self.all_three();self.assertTrue(self.g.assess(7,self.head)['all_custody_claims_are_fixtures'])
    def test_declared_no_external_network(self):self.assertEqual(self.g.expected_anchors,{})
if __name__=='__main__': unittest.main(verbosity=2)