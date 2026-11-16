import base64,copy,unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from root_auth import verify,canonical

CLAIM='a'*64;NONCE='nonce-unique-1234567890';NOW='2026-11-15T23:00:00Z';WHEN='2026-11-15T22:59:30Z'

def fixture(n=3):
    pins=[];rows=[];keys=[]
    for j in range(n):
        k=Ed25519PrivateKey.generate();keys.append(k)
        pub=k.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)
        pins.append({'id':f'w{j}','public_key':base64.b64encode(pub).decode(),'controller':f'holder-{j}',
          'platform':f'platform-{j}','source_ancestry':f'origin-{j}','status':'active'})
        b={'signer':f'w{j}','challenge':NONCE,'claim_sha256':CLAIM,'observed_at':WHEN,'choice':'observe'}
        rows.append({'body':b,'signature':base64.b64encode(k.sign(canonical(b))).decode()})
    return {'pins':pins,'statements':rows},keys

def resign(bundle,keys,index):
    r=bundle['statements'][index];r['signature']=base64.b64encode(keys[index].sign(canonical(r['body']))).decode()

class RootAuthTests(unittest.TestCase):
    def verdict(self,b,code,**kw):self.assertEqual(verify(b,NONCE,CLAIM,NOW,**kw)['verdict'],code)
    def test_success_qualified(self):
        b,_=fixture();r=verify(b,NONCE,CLAIM,NOW);self.assertEqual(r['verdict'],'DISTINCT_PINNED_SIGNERS_FIXTURE');self.assertFalse(r['independent_physical_roots_proven']);self.assertFalse(r['action_executed'])
    def test_empty(self):self.verdict({'pins':[],'statements':[]},'NO_SIGNED_RESPONSES')
    def test_one(self):b,_=fixture(1);self.verdict(b,'INSUFFICIENT_AUTHENTICATED_SIGNERS')
    def test_two(self):b,_=fixture(2);self.verdict(b,'INSUFFICIENT_AUTHENTICATED_SIGNERS')
    def test_common_controller(self):b,_=fixture();b['pins'][2]['controller']=b['pins'][0]['controller'];self.verdict(b,'SHARED_AUTHENTICATION_ANCESTRY')
    def test_common_platform(self):b,_=fixture();b['pins'][2]['platform']=b['pins'][0]['platform'];self.verdict(b,'SHARED_AUTHENTICATION_ANCESTRY')
    def test_common_ancestry(self):b,_=fixture();b['pins'][2]['source_ancestry']=b['pins'][0]['source_ancestry'];self.verdict(b,'SHARED_AUTHENTICATION_ANCESTRY')
    def test_shared_key(self):b,_=fixture();b['pins'][1]['public_key']=b['pins'][0]['public_key'];self.verdict(b,'INVALID_SIGNATURE')
    def test_duplicate_pin(self):b,_=fixture();b['pins'].append(b['pins'][0]);self.verdict(b,'DUPLICATE_PIN')
    def test_duplicate_response(self):b,_=fixture();b['statements'].append(copy.deepcopy(b['statements'][0]));self.verdict(b,'DUPLICATED_SIGNER')
    def test_invalid_signature(self):b,_=fixture();b['statements'][0]['signature']='AA==';self.verdict(b,'INVALID_SIGNATURE')
    def test_mutated_body(self):b,_=fixture();b['statements'][0]['body']['choice']='abstain';self.verdict(b,'INVALID_SIGNATURE')
    def test_replay_challenge(self):b,_=fixture();self.assertEqual(verify(b,'a-new-unrelated-nonce',CLAIM,NOW)['verdict'],'WRONG_CHALLENGE')
    def test_wrong_claim(self):b,_=fixture();self.assertEqual(verify(b,NONCE,'b'*64,NOW)['verdict'],'WRONG_CLAIM')
    def test_revoked(self):b,_=fixture();b['pins'][0]['status']='revoked';self.verdict(b,'REVOKED_SIGNER')
    def test_stale(self):b,keys=fixture();b['statements'][0]['body']['observed_at']='2026-11-15T22:00:00Z';resign(b,keys,0);self.verdict(b,'STALE_OR_FUTURE_RESPONSE')
    def test_future(self):b,keys=fixture();b['statements'][0]['body']['observed_at']='2026-11-15T23:01:00Z';resign(b,keys,0);self.verdict(b,'STALE_OR_FUTURE_RESPONSE')
    def test_invalid_choice(self):b,keys=fixture();b['statements'][0]['body']['choice']='approve';resign(b,keys,0);self.verdict(b,'INVALID_CHOICE')
    def test_bad_time(self):b,keys=fixture();b['statements'][0]['body']['observed_at']='invalid';resign(b,keys,0);self.verdict(b,'INVALID_OBSERVATION_TIME')
    def test_unpinned_signer(self):b,_=fixture();b['statements'][0]['body']['signer']='nobody';self.verdict(b,'UNPINNED_SIGNER')
    def test_bad_pin(self):b,_=fixture();b['pins'][0]['extra']=1;self.verdict(b,'INVALID_PIN')
    def test_bad_public_key(self):b,_=fixture();b['pins'][0]['public_key']='!!';self.verdict(b,'INVALID_PUBLIC_KEY')
    def test_large(self):b,_=fixture();b['statements']*=8;self.verdict(b,'INVALID_BUNDLE_SIZE')
    def test_receipt_hash_stable(self):b,_=fixture();a=verify(b,NONCE,CLAIM,NOW);self.assertEqual(a,verify(b,NONCE,CLAIM,NOW))
    def test_no_physical_proof(self):b,_=fixture();self.assertFalse(verify(b,NONCE,CLAIM,NOW)['independent_physical_roots_proven'])
    def test_no_choice(self):b,_=fixture();self.assertEqual(verify(b,NONCE,CLAIM,NOW)['collective_decision'],'UNRESOLVED')
    def test_abstention(self):b,k=fixture();b['statements'][2]['body']['choice']='abstain';resign(b,k,2);self.verdict(b,'DISTINCT_PINNED_SIGNERS_FIXTURE')
    def test_bad_bundle(self):self.assertEqual(verify({},NONCE,CLAIM,NOW)['verdict'],'INVALID_BUNDLE')
    def test_bad_clock(self):b,_=fixture();self.verdict(b,'INVALID_CLOCK',max_age_seconds=300) if False else self.assertEqual(verify(b,NONCE,CLAIM,'bad')['verdict'],'INVALID_CLOCK')
    def test_bad_expectation(self):b,_=fixture();self.assertEqual(verify(b,'no','abc',NOW)['verdict'],'INVALID_EXPECTATION')
if __name__=='__main__':unittest.main()
