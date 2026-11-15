import unittest, tempfile, os, copy
from enrollment import *

class EnrollmentTests(unittest.TestCase):
    def run_kind(self,kind,expected):
        f=FLAY219();try_result=f.audit(*fixture(kind));f.close();self.assertEqual(try_result['verdict'],expected)
    def test_valid(self):self.run_kind('valid','DECLARED_ENROLLMENT_CHAIN_CONSISTENT_FIXTURE')
    def test_self(self):self.run_kind('self','SELF_DECLARED_INSTRUMENT')
    def test_shared(self):self.run_kind('shared','SHARED_INSTRUMENT_ANCESTRY')
    def test_expired(self):self.run_kind('expired','ENROLLMENT_EXPIRED_OR_NOT_YET_VALID')
    def test_substituted(self):self.run_kind('substituted','INSTRUMENT_SIGNATURE_INVALID')
    def test_issuer(self):self.run_kind('issuer','UNTRUSTED_ENROLLMENT_ISSUER')
    def test_stale(self):self.run_kind('stale','INVALID_CAPTURE_CHRONOLOGY')
    def test_mismatch(self):self.run_kind('mismatch','RESPONSE_MISMATCH')
    def test_duplicate(self):self.run_kind('duplicate','DUPLICATE_CAPTURE')
    def test_revoked(self):self.run_kind('revoked','REVOKED_INSTRUMENT')
    def test_forged(self):self.run_kind('forged','INSTRUMENT_SIGNATURE_INVALID')
    def test_insufficient(self):self.run_kind('insufficient','INSUFFICIENT_ENROLLED_INSTRUMENTS')
    def test_replay(self):
        f=FLAY219(); f.audit(*fixture());self.assertEqual(f.audit(*fixture())['verdict'],'REPLAY_CHALLENGE');f.close()
    def test_replay_restart(self):
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,'log.db');f=FLAY219(path);f.audit(*fixture());f.close();f=FLAY219(path);self.assertEqual(f.audit(*fixture())['verdict'],'REPLAY_CHALLENGE');f.close()
    def test_valid_count(self):
        f=FLAY219();r=f.audit(*fixture());self.assertEqual(r['count'],2);self.assertFalse(r['physical_identity_proven']);f.close()
    def test_tampered_challenge(self):
        a=list(fixture());a[0]['body']['release']=5;f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'CHALLENGE_SIGNATURE_INVALID');f.close()
    def test_tampered_enrollment(self):
        a=list(fixture());a[2][0]['body']['sensor']='changed';f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'UNTRUSTED_ENROLLMENT_ISSUER');f.close()
    def test_tampered_capture(self):
        a=list(fixture());a[1][0]['body']['capture']=140;f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'INSTRUMENT_SIGNATURE_INVALID');f.close()
    def test_wrong_signer_key(self):
        a=list(fixture());a[1][0]['signature']=sign(a[1][0]['body'],'attacker')['signature'];f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'INSTRUMENT_SIGNATURE_INVALID');f.close()
    def test_bad_issuer_configuration(self):
        f=FLAY219(trusted_issuers={'enrollment-authority':public('attacker')});self.assertEqual(f.audit(*fixture())['verdict'],'UNTRUSTED_ENROLLMENT_ISSUER');f.close()
    def test_malformed(self):
        f=FLAY219();self.assertEqual(f.audit({},[],[])['verdict'],'MALFORMED_EVIDENCE');f.close()
    def test_invalid_nonce(self):
        a=list(fixture(nonce='x'));f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'INVALID_NONCE');f.close()
    def test_empty_acquisitions(self):
        a=list(fixture());a[1]=[];f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'INSUFFICIENT_ENROLLED_INSTRUMENTS');f.close()
    def test_unsupported_type(self):
        a=list(fixture());a[1]='bad';f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'MALFORMED_EVIDENCE');f.close()
    def test_invalid_chronology(self):
        a=list(fixture());a[0]=sign({**a[0]['body'],'freeze':125},'challenger');f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'INVALID_CHRONOLOGY');f.close()
    def test_capture_too_late(self):
        a=list(fixture());a[1][1]=sign({**a[1][1]['body'],'capture':151},'instrument-1');f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'INVALID_CAPTURE_CHRONOLOGY');f.close()
    def test_enrollment_future(self):
        a=list(fixture());a[2][1]=sign({**a[2][1]['body'],'not_before':140},'enrollment-authority');f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'ENROLLMENT_EXPIRED_OR_NOT_YET_VALID');f.close()
    def test_invalid_enrollment_window(self):
        a=list(fixture());a[2][1]=sign({**a[2][1]['body'],'not_after':40},'enrollment-authority');f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'INVALID_ENROLLMENT_WINDOW');f.close()
    def test_duplicate_enrollment(self):
        a=list(fixture());a[2].append(a[2][0]);f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'DUPLICATE_ENROLLMENT');f.close()
    def test_invalid_revocation(self):
        a=list(fixture());a[3]=[sign({'issuer':'enrollment-authority','device_id':'instrument-0','effective_at':90},'attacker')];f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'INVALID_REVOCATION');f.close()
    def test_future_revocation_allows(self):
        a=list(fixture());a[3]=[sign({'issuer':'enrollment-authority','device_id':'instrument-0','effective_at':145},'enrollment-authority')];f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'DECLARED_ENROLLMENT_CHAIN_CONSISTENT_FIXTURE');f.close()
    def test_duplicate_revocation(self):
        a=list(fixture());rev=sign({'issuer':'enrollment-authority','device_id':'instrument-0','effective_at':90},'enrollment-authority');a[3]=[rev,rev];f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'CONFLICTING_REVOCATIONS');f.close()
    def test_declared_sensor_overlap(self):
        a=list(fixture());a[2][1]=sign({**a[2][1]['body'],'sensor':'sensor-0'},'enrollment-authority');f=FLAY219();self.assertEqual(f.audit(*a)['verdict'],'SHARED_INSTRUMENT_ANCESTRY');f.close()
    def test_default_policy(self): self.assertEqual(Policy().min_instruments,2)
    def test_public_32bytes(self):self.assertEqual(len(bytes.fromhex(public('instrument-0'))),32)
    def test_verify_bad_sig(self):self.assertFalse(verify({'body':{},'signature':'bad'},public('challenger')))
    def test_canonical(self):self.assertEqual(canon({'b':2,'a':1}),canon({'a':1,'b':2}))
    def test_digest_stable(self):self.assertEqual(digest('a'),digest('a'))
    def test_result_hash(self):
        f=FLAY219();f.audit(*fixture());self.assertTrue(f.verify_log());f.close()
    def test_alt_policy(self):
        f=FLAY219(policy=Policy(min_instruments=3));self.assertEqual(f.audit(*fixture())['verdict'],'INSUFFICIENT_ENROLLED_INSTRUMENTS');f.close()
    def test_signature_stable_fixture(self):self.assertEqual(sign({'x':1},'challenger'),sign({'x':1},'challenger'))

if __name__=='__main__':unittest.main()
