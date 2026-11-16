import base64
import copy
import unittest
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from custody import audit, canonical, digest
NOW='2026-11-15T20:00:00Z'
CHALLENGE='a'*64
K1='1'*64
K2='2'*64

def pub(k):
    return base64.b64encode(k.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)).decode()

def sign(k,body):return base64.b64encode(k.sign(canonical(body))).decode()

class CustodyTests(unittest.TestCase):
    def setUp(self):
        self.keys={n:Ed25519PrivateKey.generate() for n in ('reg','audit1','audit2','security')}
        self.bundle={'subject':'jane-demo','challenge':CHALLENGE,'anchors':{n:{'public_key':pub(self.keys[n]),'trust_root':n,'role':role} for n,role in [('reg','registrar'),('audit1','custody_auditor'),('audit2','custody_auditor'),('security','security_operator')]},'events':[]}
        self.add('ENROLLED','reg',K1)
        self.add('CUSTODY_ATTESTED','audit1',K1)
        self.add('CUSTODY_ATTESTED','audit2',K1)
    def add(self,kind,signer,key,replacement=None):
        b={'id':f'e{len(self.bundle["events"])}','subject':'jane-demo','event':kind,'key_fingerprint':key,'replacement_fingerprint':replacement,'time':(datetime(2026,11,15,19,0,tzinfo=timezone.utc)+timedelta(seconds=len(self.bundle['events']))).isoformat(),'challenge':CHALLENGE,'prev':digest(self.bundle['events'][-1]) if self.bundle['events'] else '0'*64}
        self.bundle['events'].append({'body':b,'signer':signer,'signature':sign(self.keys[signer],b)})
    def check(self):return audit(self.bundle,NOW)['verdict']
    def test_good_claim_still_not_proof(self):
        x=audit(self.bundle,NOW)
        self.assertEqual(x['verdict'],'SIGNED_CUSTODY_CLAIMS_CONSISTENT_NOT_PROVEN');self.assertFalse(x['exclusive_custody_proven']);self.assertEqual(x['jane_collective_choice'],'UNRESOLVED')
    def test_empty(self):self.bundle['events']=[];self.assertEqual(self.check(),'NO_CUSTODY_EVIDENCE')
    def test_broken_signature(self):self.bundle['events'][1]['signature']='AA==';self.assertEqual(self.check(),'INVALID_SIGNATURE')
    def test_unknown_signer(self):self.bundle['events'][1]['signer']='unknown';self.assertEqual(self.check(),'UNKNOWN_SIGNER')
    def test_subject_mismatch(self):self.bundle['events'][1]['body']['subject']='other';self._resign(1);self.assertEqual(self.check(),'CHALLENGE_OR_SUBJECT_MISMATCH')
    def test_challenge_mismatch(self):self.bundle['events'][1]['body']['challenge']='b'*64;self._resign(1);self.assertEqual(self.check(),'CHALLENGE_OR_SUBJECT_MISMATCH')
    def _resign(self,i):
        e=self.bundle['events'][i];e['signature']=sign(self.keys[e['signer']],e['body'])
        for j in range(i+1,len(self.bundle['events'])):
            self.bundle['events'][j]['body']['prev']=digest(self.bundle['events'][j-1]);self._resign_only(j)
    def _resign_only(self,i):
        e=self.bundle['events'][i];e['signature']=sign(self.keys[e['signer']],e['body'])
    def test_broken_chain(self):self.bundle['events'][2]['body']['prev']='b'*64;self._resign_only(2);self.assertEqual(self.check(),'BROKEN_EVENT_CHAIN')
    def test_replay(self):self.bundle['events'][1]['body']['id']='e0';self._resign(1);self.assertEqual(self.check(),'REPLAYED_EVENT')
    def test_unknown_event(self):self.bundle['events'][1]['body']['event']='CLEAR';self._resign(1);self.assertEqual(self.check(),'UNKNOWN_EVENT_TYPE')
    def test_future(self):self.bundle['events'][1]['body']['time']='2026-11-16T21:00:00Z';self._resign(1);self.assertEqual(self.check(),'STALE_OR_FUTURE_EVENT')
    def test_stale(self):self.assertEqual(audit(self.bundle,'2026-11-20T20:00:00Z')['verdict'],'STALE_OR_FUTURE_EVENT')
    def test_backdated(self):self.bundle['events'][2]['body']['time']='2026-11-15T18:00:00Z';self._resign(2);self.assertEqual(self.check(),'NONMONOTONIC_EVENT_TIME')
    def test_wrong_key(self):self.bundle['events'][2]['body']['key_fingerprint']=K2;self._resign(2);self.assertEqual(self.check(),'KEY_LINEAGE_MISMATCH')
    def test_wrong_role(self):self.bundle['events'][1]['signer']='reg';self._resign(1);self.assertEqual(self.check(),'UNAUTHORIZED_EVENT_SIGNER')
    def test_two_names_one_root(self):self.bundle['anchors']['audit2']['trust_root']='audit1';self.assertEqual(self.check(),'INSUFFICIENT_DISTINCT_ATTESTOR_ROOTS')
    def test_duplicated_public_key(self):self.bundle['anchors']['audit2']['public_key']=self.bundle['anchors']['audit1']['public_key'];self.assertEqual(self.check(),'SHARED_SIGNING_KEY')
    def test_exposure(self):self.add('EXPOSURE_SUSPECTED','security',K1);self.assertEqual(self.check(),'KEY_EXPOSURE_REPORTED')
    def test_confirmed_exposure(self):self.add('EXPOSURE_CONFIRMED','security',K1);self.assertEqual(self.check(),'KEY_EXPOSURE_REPORTED')
    def test_exposure_cannot_be_undone_by_attestation(self):self.add('EXPOSURE_SUSPECTED','security',K1);self.add('CUSTODY_ATTESTED','audit1',K1);self.assertEqual(self.check(),'KEY_EXPOSURE_REPORTED')
    def test_revocation(self):self.add('REVOKED','reg',K1);self.assertEqual(self.check(),'KEY_REVOKED')
    def test_rotation_requires_new_attestation(self):self.add('ROTATED','reg',K1,K2);self.assertEqual(self.check(),'INSUFFICIENT_DISTINCT_ATTESTOR_ROOTS')
    def test_rotation_with_new_attestations(self):self.add('ROTATED','reg',K1,K2);self.add('CUSTODY_ATTESTED','audit1',K2);self.add('CUSTODY_ATTESTED','audit2',K2);self.assertEqual(self.check(),'SIGNED_CUSTODY_CLAIMS_CONSISTENT_NOT_PROVEN')
    def test_rotation_to_same_key(self):self.add('ROTATED','reg',K1,K1);self.assertEqual(self.check(),'INVALID_ROTATION')
    def test_malformed_pubkey(self):self.bundle['anchors']['reg']['public_key']='bad';self.assertEqual(self.check(),'INVALID_TRUST_CONFIGURATION')
    def test_unauthorized_exposure_signer(self):self.add('EXPOSURE_CONFIRMED','reg',K1);self.assertEqual(self.check(),'UNAUTHORIZED_EVENT_SIGNER')
    def test_bad_fingerprint(self):self.bundle['events'][0]['body']['key_fingerprint']='not-a-hash';self._resign(0);self.assertEqual(self.check(),'INVALID_KEY_FINGERPRINT')
    def test_wrong_challenge_shape(self):self.bundle['challenge']='bad';self.assertEqual(self.check(),'INVALID_BUNDLE')
    def test_max_events(self):self.assertEqual(audit(self.bundle,NOW,max_events=2)['verdict'],'INVALID_BUNDLE')
    def test_extra_untrusted_field(self):self.bundle['events'][0]['body']['self_attested_secrecy']=True;self._resign(0);self.assertEqual(self.check(),'INVALID_EVENT')
    def test_no_auto_actions(self):self.assertEqual(audit(self.bundle,NOW)['actions_executed'],0)
    def test_non_zoned_timestamp(self):self.bundle['events'][1]['body']['time']='2026-11-15T19:00:01';self._resign(1);self.assertEqual(self.check(),'INVALID_EVENT_TIME')
    def test_untrusted_registrar(self):self.bundle['anchors']['reg']['role']='custody_auditor';self.assertEqual(self.check(),'UNAUTHORIZED_EVENT_SIGNER')
    def test_missing_anchor(self):del self.bundle['anchors']['audit1'];self.assertEqual(self.check(),'UNKNOWN_SIGNER')

if __name__=='__main__':unittest.main()
