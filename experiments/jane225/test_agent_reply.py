import copy, hashlib, json, os, tempfile, unittest
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from agent_reply import challenge, signed_response, verify, ReplayStore, b64, aggregate, canonical

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.db=self.tmp.name+'/audit.sqlite3'; self.store=ReplayStore(self.db); self.addCleanup(self.store.close)
        self.private=Ed25519PrivateKey.generate()
        self.public=b64(self.private.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw))
        now=datetime(2026,11,15,20,0,tzinfo=timezone.utc); self.now=now
        self.req=challenge('aci:nom', 'x'*32,(now-timedelta(minutes=1)).isoformat(),(now+timedelta(minutes=1)).isoformat(),hashlib.sha256(b'what would you choose?').hexdigest())
        self.trust={'aci:nom':{'public_key_b64':self.public,'enabled':True}}
        self.packet=signed_response(self.private,self.req,'abstain',reason='No conversational choice interface.')
    def check(self,verdict,packet=None,req=None,trust=None):
        self.assertEqual(verify(self.packet if packet is None else packet,self.req if req is None else req,self.trust if trust is None else trust,self.store,now=self.now)['verdict'],verdict)
    def test_valid_abstain(self): self.check('AUTHENTICATED_COMPONENT_RESPONSE')
    def test_valid_propose(self): self.check('AUTHENTICATED_COMPONENT_RESPONSE',signed_response(self.private,self.req,'propose','audit one source','deterministic'))
    def test_replay(self): self.check('AUTHENTICATED_COMPONENT_RESPONSE'); self.check('REPLAY')
    def test_restart(self):
        self.check('AUTHENTICATED_COMPONENT_RESPONSE'); self.store.close(); self.store=ReplayStore(self.db);self.addCleanup(self.store.close);self.check('REPLAY')
    def test_no_trust(self): self.check('UNTRUSTED_RUNTIME',trust={'aci:nom':{'enabled':False}})
    def test_mismatched_agent(self):
        p=copy.deepcopy(self.packet);p['payload']['agent_id']='aci:jane'; self.check('CHALLENGE_MISMATCH',p)
    def test_mismatched_nonce(self):
        p=copy.deepcopy(self.packet);p['payload']['nonce']='z'*32; self.check('CHALLENGE_MISMATCH',p)
    def test_tamper_signature(self):
        p=copy.deepcopy(self.packet);p['payload']['reason']='I love doing that';self.check('INVALID_SIGNATURE_OR_KEY',p)
    def test_invalid_key(self): self.check('INVALID_SIGNATURE_OR_KEY',trust={'aci:nom':{'enabled':True,'public_key_b64':b64(b'0'*32)}})
    def test_wrong_question(self):
        req=copy.deepcopy(self.req);req['question_sha256']='f'*64;self.check('CHALLENGE_MISMATCH',req=req)
    def test_expired(self): self.req['expires_at']=(self.now-timedelta(seconds=1)).isoformat();self.check('STALE_OR_FUTURE_CHALLENGE',packet=signed_response(self.private,self.req,'abstain'))
    def test_future(self): self.req['issued_at']=(self.now+timedelta(seconds=1)).isoformat();self.check('STALE_OR_FUTURE_CHALLENGE',packet=signed_response(self.private,self.req,'abstain'))
    def test_long_window(self): self.req['expires_at']=(self.now+timedelta(hours=2)).isoformat();self.check('BAD_CHALLENGE_WINDOW',packet=signed_response(self.private,self.req,'abstain'))
    def test_backward_window(self): self.req['expires_at']=(self.now-timedelta(minutes=2)).isoformat();self.check('BAD_CHALLENGE_WINDOW',packet=signed_response(self.private,self.req,'abstain'))
    def test_weak_nonce(self): self.req['nonce']='x';self.check('WEAK_CHALLENGE_NONCE')
    def test_bad_question(self): self.req['question_sha256']='abc';self.check('BAD_QUESTION_HASH')
    def test_bad_schema(self): self.req['schema']='other';self.check('BAD_SCHEMA')
    def test_extra_req_field(self): self.req['extra']=1;self.check('MALFORMED_CHALLENGE')
    def test_extra_response_field(self):
        p=copy.deepcopy(self.packet);p['extra']=1;self.check('EXTRA_PACKET_FIELDS',p)
    def test_extra_payload_field(self):
        p=copy.deepcopy(self.packet);p['payload']['extra']=1;self.check('MALFORMED_RESPONSE',p)
    def test_bad_decision(self):
        p=signed_response(self.private,self.req,'propose','x');p['payload']['decision']='execute';self.check('INVALID_DECISION',p)
    def test_conflicting_abstention(self):
        p=copy.deepcopy(self.packet);p['payload']['proposal']='do it';self.check('ABSTENTION_CONFLICT',p)
    def test_empty_proposal(self):
        p=signed_response(self.private,self.req,'propose','x');p['payload']['proposal']='  ';self.check('EMPTY_PROPOSAL',p)
    def test_oversize(self):
        p=signed_response(self.private,self.req,'propose','x'*2001);self.check('OVERSIZE_RESPONSE',p)
    def test_signed_output_never_authorizes(self):
        v=verify(self.packet,self.req,self.trust,self.store,now=self.now);self.assertEqual(v['collective_decision'],'UNRESOLVED');self.assertFalse(v['action_executed'])
    def test_aggregation_no_votes(self):
        self.assertEqual(aggregate([{'verdict':'AUTHENTICATED_COMPONENT_RESPONSE'}]*3)['collective_decision'],'UNRESOLVED')
    def test_empty_aggregation(self): self.assertEqual(aggregate([])['collective_decision'],'UNRESOLVED')
    def test_bad_signature_doesnt_use_nonce(self):
        p=copy.deepcopy(self.packet);p['payload']['reason']='wrong';self.check('INVALID_SIGNATURE_OR_KEY',p);self.check('AUTHENTICATED_COMPONENT_RESPONSE')
    def test_signed_abstention_has_no_proposal(self): self.assertEqual(self.packet['payload']['proposal'],'')
    def test_no_agent_impersonation(self):
        self.req['agent_id']='aci:jane';self.check('CHALLENGE_MISMATCH')
    def test_hash_is_sha256(self): self.assertEqual(len(self.packet['payload']['request_sha256']),64)
    def test_bad_clock(self): self.assertEqual(verify(self.packet,self.req,self.trust,self.store,now=datetime(2026,11,15))['verdict'],'BAD_CLOCK')
    def test_no_untrusted_key_consumption(self):
        self.check('UNTRUSTED_RUNTIME',trust={});self.check('AUTHENTICATED_COMPONENT_RESPONSE')

if __name__=='__main__':unittest.main()