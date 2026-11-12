import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from pathlib import Path
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from enrollment import Enrollment, Authority, CHRONOS, utc, canonical


def pub(k):
    return k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)

class EnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)
        self.now=utc(CHRONOS,-360)
        self.ops=[Ed25519PrivateKey.generate() for _ in range(3)]
        self.authkeys=[Ed25519PrivateKey.generate() for _ in range(3)]
        self.auth={f'a{i}':Authority(f'a{i}',pub(k),f'admin{i}') for i,k in enumerate(self.authkeys)}
        self.obj=Enrollment(self.path/'state.db',self.path/'anchor.json',self.auth)
        self.nonce='fixed-nonce-00000001'
    def tearDown(self):
        self.obj.db.close();self.temp.cleanup()
    def create_challenge(self, **kwargs):
        params=dict(nonce=self.nonce,operator='operator-one',root='external:one',public=pub(self.ops[0]),stamp=CHRONOS,offset=-360,now=self.now)
        params.update(kwargs)
        return self.obj.challenge(**params)
    def approvals(self,indices=(0,1),operator='operator-one',root='external:one',key_id='w0',public=None):
        public=public or pub(self.ops[0])
        binding=dict(domain='JANE-146-ENROLL',nonce=self.nonce,key_id=key_id,operator=operator,root=root,public_sha256=sha256(public).hexdigest(),chronos=CHRONOS,utc_offset=-360)
        sig=self.ops[0].sign(canonical(binding))
        approvals=[]
        for i in indices:
            aid=f'a{i}'
            approvals.append((aid,self.authkeys[i].sign(canonical(dict(domain='JANE-146-APPROVE',binding=binding,authority=aid)))))
        return sig,approvals
    def enroll(self,indices=(0,1)):
        self.assertEqual(self.create_challenge(),'CHALLENGE_ISSUED')
        sig,approvals=self.approvals(indices)
        return self.obj.enroll(self.nonce,'w0',sig,approvals,self.now)
    def rotation(self,signer=None,nonce='rotate-nonce-000001',key_id='w1',new=None):
        new=new or self.ops[1];signer=signer or self.ops[0]
        body=dict(domain='JANE-146-ROTATE',root='external:one',old_key='w0',new_key=key_id,new_public_sha256=sha256(pub(new)).hexdigest(),generation=1,nonce=nonce,chronos=CHRONOS,utc_offset=-360)
        return self.obj.rotate('external:one',key_id,pub(new),nonce,CHRONOS,-360,signer.sign(canonical(body)),self.now)

    def test_valid_challenge(self):self.assertEqual(self.create_challenge(),'CHALLENGE_ISSUED')
    def test_valid_enrollment(self):self.assertEqual(self.enroll(),'ENROLLED_REGISTRY_CLAIM')
    def test_registry_record(self):self.enroll();self.assertEqual(self.obj.custody()[0]['operator'],'operator-one')
    def test_one_root(self):self.enroll();self.assertEqual(self.obj.report()['root_count'],1)
    def test_operational_independence_not_claimed(self):self.enroll();self.assertEqual(self.obj.report()['operational_independence'],'UNVERIFIED')
    def test_jane_unmoved(self):self.enroll();self.assertFalse(self.obj.report()['learning_applied'])
    def test_replay_challenge(self):self.create_challenge();self.assertEqual(self.create_challenge(),'REPLAY')
    def test_replay_enrollment(self):
        self.enroll();sig,approvals=self.approvals();self.assertEqual(self.obj.enroll(self.nonce,'w0',sig,approvals,self.now),'REPLAY')
    def test_duplicate_root(self):
        self.enroll();self.assertEqual(self.create_challenge(nonce='another-nonce-00001'),'IDENTITY_ALREADY_ENROLLED')
    def test_duplicate_operator(self):
        self.enroll();self.assertEqual(self.create_challenge(nonce='another-nonce-00001',root='external:two'),'IDENTITY_ALREADY_ENROLLED')
    def test_one_attestor(self):self.assertEqual(self.enroll((0,)),'INSUFFICIENT_ATTESTATION')
    def test_zero_attestor(self):self.assertEqual(self.enroll(()),'INSUFFICIENT_ATTESTATION')
    def test_repeated_attestor(self):self.assertEqual(self.enroll((0,0)),'INSUFFICIENT_ATTESTATION')
    def test_shared_admin_root(self):
        a=self.auth['a1'];self.auth['a1']=replace(a,administrative_root='admin0');self.obj.authorities=self.auth
        self.assertEqual(self.enroll(),'INSUFFICIENT_ATTESTATION')
    def test_unknown_attestor(self):
        self.create_challenge();sig,approvals=self.approvals()
        self.assertEqual(self.obj.enroll(self.nonce,'w0',sig,[('unknown',approvals[0][1]),approvals[1]],self.now),'INSUFFICIENT_ATTESTATION')
    def test_fake_possession(self):
        self.create_challenge();_,approvals=self.approvals()
        self.assertEqual(self.obj.enroll(self.nonce,'w0',self.ops[2].sign(b'lie'),approvals,self.now),'FAILED_KEY_POSSESSION')
    def test_wrong_operator_claim(self):
        self.create_challenge();sig,approvals=self.approvals(operator='other')
        self.assertEqual(self.obj.enroll(self.nonce,'w0',sig,approvals,self.now),'FAILED_KEY_POSSESSION')
    def test_expiration(self):
        self.create_challenge();sig,approvals=self.approvals()
        self.assertEqual(self.obj.enroll(self.nonce,'w0',sig,approvals,self.now+timedelta(minutes=6)),'EXPIRED_CHALLENGE')
    def test_stale_chronos(self):self.assertEqual(self.create_challenge(now=self.now+timedelta(hours=1)),'STALE_CHRONOS')
    def test_invalid_date(self):self.assertEqual(self.create_challenge(stamp=CHRONOS.replace('11.12','02.30')),'INVALID_CHRONOS')
    def test_invalid_angle(self):self.assertEqual(self.create_challenge(stamp=CHRONOS.replace('123.45.56','123.60.56')),'INVALID_CHRONOS')
    def test_invalid_offset(self):self.assertEqual(self.create_challenge(offset=900),'INVALID_CHRONOS')
    def test_bad_nonce(self):self.assertEqual(self.create_challenge(nonce='short'),'INVALID_CHALLENGE')
    def test_invalid_key_size(self):self.assertEqual(self.create_challenge(public=b'x'),'INVALID_CHALLENGE')
    def test_unknown_challenge(self):self.assertEqual(self.obj.enroll('never','w0',b'x',[],self.now),'UNKNOWN_CHALLENGE')
    def test_rotate_valid(self):self.enroll();self.assertEqual(self.rotation(),'ROTATED_SAME_CUSTODY')
    def test_generation_increment(self):self.enroll();self.rotation();self.assertEqual(self.obj.custody()[0]['generation'],1)
    def test_rotation_no_new_custody(self):self.enroll();self.rotation();self.assertEqual(len(self.obj.custody()),1)
    def test_rotation_impersonation(self):self.enroll();self.assertEqual(self.rotation(signer=self.ops[2]),'FAILED_ROTATION_SIGNATURE')
    def test_rotation_nonce_replay(self):self.enroll();self.rotation();self.assertEqual(self.obj.db.execute('SELECT COUNT(*) FROM used').fetchone()[0],1)
    def test_rotation_double_same_key(self):self.enroll();self.rotation();self.assertEqual(self.obj.custody()[0]['key_id'],'w1')
    def test_restart_registry(self):
        self.enroll();self.obj.db.close();self.obj=Enrollment(self.path/'state.db',self.path/'anchor.json',self.auth)
        self.assertEqual(self.obj.custody()[0]['key_id'],'w0')
    def test_restart_replay_challenge(self):
        self.create_challenge();self.obj.db.close();self.obj=Enrollment(self.path/'state.db',self.path/'anchor.json',self.auth)
        self.assertEqual(self.create_challenge(),'REPLAY')
    def test_hash_chain(self):self.enroll();self.assertEqual(self.obj.audit(),'VALID_LOCAL_CHAIN_ONLY')
    def test_tamper(self):
        self.enroll();self.obj.db.execute("UPDATE history SET kind='FORGED' WHERE seq=0");self.obj.db.commit()
        self.assertEqual(self.obj.audit(),'TAMPERED')
    def test_anchor_match(self):self.enroll();self.obj.export_anchor();self.assertEqual(self.obj.audit(),'MATCHED_LOCAL_ANCHOR')
    def test_anchor_fork(self):self.enroll();self.obj.export_anchor();self.rotation();self.assertEqual(self.obj.audit(),'ROLLBACK_OR_FORK')
    def test_deterministic_binding(self):
        self.create_challenge();self.assertEqual(self.approvals()[0],self.approvals()[0])
    def test_chronos_utc(self):self.assertEqual(self.now.hour,23)
    def test_negative_budget(self):
        with self.assertRaises(ValueError):Enrollment(self.path/'x.db',self.path/'head2.json',self.auth,max_skew=-1)
    def test_no_authority(self):
        with self.assertRaises(ValueError):Enrollment(self.path/'x.db',self.path/'head2.json',{})
    def test_report_frozen_parent(self):self.assertEqual(self.obj.report()['active'],'frozen_parent')
    def test_anchor_separate_storage_path(self):self.assertNotEqual(self.obj.anchor_file, self.path/'state.db')

if __name__ == '__main__':unittest.main(verbosity=2)