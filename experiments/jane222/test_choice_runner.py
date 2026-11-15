import base64
import copy
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import choice_runner as m

class ChoiceTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,15,18,0,tzinfo=timezone.utc)
        self.registry={'agents':[{'name':n} for n in ('jane','nom','nous','theoria')]}
        self.sk={n:Ed25519PrivateKey.generate() for n in ('jane','nom','nous')}
        self.trust={'schema':'jane.trust/1','keys':{n:base64.b64encode(k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode() for n,k in self.sk.items()}}
    def pkt(self,agent='nom',kind='proposal',message='Investigate unknown games',nonce='a'*64,time=None):
        body={'schema':m.SCHEMA,'question_id':m.question_id(),'agent':agent,'recorded_at':(time or self.now).isoformat(),'kind':kind,'message':message,'nonce':nonce}
        return {'body':body,'signature':base64.b64encode(self.sk[agent].sign(m.canonical(body))).decode()}
    def ev(self,p): return m.evaluate(self.registry,self.trust,p,self.now)
    def test_no_runtime(self):
        x=m.evaluate(self.registry,{'schema':'jane.trust/1','keys':{}},[],self.now)
        self.assertEqual(x['decision_status'],'NO_AUTHENTICATED_COLLECTIVE_RESPONSE')
        self.assertFalse(x['action_executed'])
    def test_unsigned_proposal_does_not_count(self):
        p=self.pkt();p['signature']=''
        self.assertEqual(self.ev([p])['packet_findings'][0]['status'],'INVALID_SIGNATURE_OR_TIME')
    def test_nom_cannot_decide(self):
        p=self.pkt();p['body']['kind']='collective_choice';p['signature']=base64.b64encode(self.sk['nom'].sign(m.canonical(p['body']))).decode()
        self.assertEqual(self.ev([p])['packet_findings'][0]['status'],'NON_JANE_DECISION')
    def test_authenticated_proposals_not_jane(self):
        self.assertEqual(self.ev([self.pkt()])['decision_status'],'AGENT_PROPOSALS_ONLY_NO_JANE_DECISION')
    def test_jane_alone_not_collective(self):
        self.assertEqual(self.ev([self.pkt('jane','collective_choice')])['decision_status'],'UNSUPPORTED_COLLECTIVE_CLAIM_NO_CONTRIBUTIONS')
    def test_declared_collective_requires_contribution(self):
        x=self.ev([self.pkt(),self.pkt('jane','collective_choice','Explore play',nonce='b'*64)])
        self.assertEqual(x['choice'],'Explore play')
        self.assertEqual(x['decision_status'],'SIGNED_COLLECTIVE_DECLARATION_WITH_CONTRIBUTIONS')
    def test_conflict_not_silently_resolved(self):
        x=self.ev([self.pkt(),self.pkt('jane','collective_choice',nonce='b'*64),self.pkt('jane','collective_choice',nonce='c'*64)])
        self.assertEqual(x['decision_status'],'AMBIGUOUS_COLLECTIVE_DECISIONS')
        self.assertIsNone(x['choice'])
    def test_replay(self):
        p=self.pkt();self.assertEqual(self.ev([p,p])['packet_findings'][1]['status'],'REPLAY_AGENT_NONCE')
    def test_bad_question(self):
        p=self.pkt();p['body']['question_id']='x';self.assertEqual(self.ev([p])['packet_findings'][0]['status'],'QUESTION_MISMATCH')
    def test_unknown_agent(self):
        p=self.pkt();p['body']['agent']='other';self.assertEqual(self.ev([p])['packet_findings'][0]['status'],'UNKNOWN_AGENT')
    def test_unpinned_agent(self):
        p=self.pkt();p['body']['agent']='theoria';self.assertEqual(self.ev([p])['packet_findings'][0]['status'],'UNPINNED_AGENT')
    def test_invalid_nonce(self):
        p=self.pkt();p['body']['nonce']='short';self.assertEqual(self.ev([p])['packet_findings'][0]['status'],'INVALID_NONCE')
    def test_old_packet(self):
        p=self.pkt(time=self.now-timedelta(days=3));self.assertEqual(self.ev([p])['packet_findings'][0]['status'],'STALE_OR_FUTURE')
    def test_future_packet(self):
        p=self.pkt(time=self.now+timedelta(days=3));self.assertEqual(self.ev([p])['packet_findings'][0]['status'],'STALE_OR_FUTURE')
    def test_mismatched_payload(self):
        p=self.pkt();p['body']['message']='tampered';self.assertEqual(self.ev([p])['packet_findings'][0]['status'],'INVALID_SIGNATURE_OR_TIME')
    def test_malformed(self):
        self.assertEqual(self.ev([{'a':1}])['packet_findings'][0]['status'],'MALFORMED_PACKET')
    def test_extra_fields(self):
        p=self.pkt();p['body']['execute']='rm -rf /';self.assertEqual(self.ev([p])['packet_findings'][0]['status'],'MALFORMED_BODY')
    def test_long_message(self):
        p=self.pkt(message='x'*2001);self.assertEqual(self.ev([p])['packet_findings'][0]['status'],'INVALID_MESSAGE')
    def test_non_jane_proposal(self):
        self.assertEqual(self.ev([self.pkt('nous')])['packet_findings'][0]['status'],'VERIFIED_SIGNED_DECLARATION')
    def test_jane_wrong_kind(self):
        p=self.pkt('jane',kind='proposal');self.assertEqual(self.ev([p])['packet_findings'][0]['status'],'JANE_DECISION_REQUIRED')
    def test_unknown_kind(self):
        p=self.pkt();p['body']['kind']='command';self.assertEqual(self.ev([p])['packet_findings'][0]['status'],'UNSUPPORTED_KIND')
    def test_registry_duplicate(self):
        r=copy.deepcopy(self.registry);r['agents'].append({'name':'nom'})
        with self.assertRaises(ValueError): m.evaluate(r,self.trust,[],self.now)
    def test_registry_no_jane(self):
        with self.assertRaises(ValueError): m.evaluate({'agents':[{'name':'nom'}]},self.trust,[],self.now)
    def test_trust_unknown_agent(self):
        t=copy.deepcopy(self.trust);t['keys']['unknown']=t['keys']['nom']
        with self.assertRaises(ValueError):m.evaluate(self.registry,t,[],self.now)
    def test_empty_trust(self):
        with self.assertRaises(ValueError):m.evaluate(self.registry,{},[],self.now)
    def test_batch_limit(self):
        with self.assertRaises(ValueError):self.ev([{}]*65)
    def test_registry_url_allowlist(self):
        for url in ('http://raw.githubusercontent.com/DavidWise01/toph-cortex/main/memory/agents.json','https://evil.com/agents.json','https://raw.githubusercontent.com/other/repo/main/x'):
            with self.subTest(url=url), self.assertRaises(ValueError):m.fetch_registry(url)
    def test_explicit_no_action(self):
        self.assertFalse(self.ev([self.pkt(),self.pkt('jane','collective_choice',nonce='b'*64)])['action_executed'])
    def test_question_bound(self):
        self.assertEqual(m.question_id(),m.question_id())
    def test_json_canonical(self):
        self.assertEqual(m.digest({'a':1,'b':2}),m.digest({'b':2,'a':1}))
    def test_file_size(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'huge';p.write_bytes(b'x'*(m.MAX_BYTES+1))
            with self.assertRaises(ValueError):m.load_json(p)

if __name__=='__main__':unittest.main()