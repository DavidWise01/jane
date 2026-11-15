import copy
import json
import unittest
from datetime import datetime
from nom_bridge import audit, observe

BASE={'wiki':'https://en.wikipedia.org/wiki/Topology','wiki_rev':'2026-01-01T00:00:00Z',
      'arxiv':'https://arxiv.org/abs/2606.10001v1','arxiv_title':'Title',
      'arxiv_pub':'2026-06-02T00:00:00Z','verdict':'NEW','read':'2026-06-03T00:00:00Z'}
COMMIT='a'*40
REG={'agents':[{'name':'nom'},{'name':'jane'}]}
def raw(r=BASE): return (json.dumps(r)+'\n').encode()

class TestNomBridge(unittest.TestCase):
    def test_valid(self): self.assertEqual(audit(raw())['count'],1)
    def test_empty(self): self.assertEqual(audit(b'')['count'],0)
    def test_sha_consistent(self): self.assertEqual(audit(raw())['ledger_sha256'], audit(raw())['ledger_sha256'])
    def test_many(self): self.assertEqual(audit(raw()*4)['count'],4)
    def test_truncated(self):
        with self.assertRaises(ValueError): audit(raw()[:-1])
    def test_bad_json(self):
        with self.assertRaises(ValueError): audit(b'{bad}\n')
    def test_blank(self):
        with self.assertRaises(ValueError): audit(b'\n')
    def test_oversize(self):
        with self.assertRaises(ValueError): audit(b'x'*(2_000_001))
    def test_not_bytes(self):
        with self.assertRaises(ValueError): audit('hello')
    def test_missing_field(self):
        x=copy.deepcopy(BASE);x.pop('wiki')
        with self.assertRaises(ValueError):audit(raw(x))
    def test_wrong_field_type(self):
        x=copy.deepcopy(BASE);x['wiki_rev']=1
        with self.assertRaises(ValueError):audit(raw(x))
    def test_http_rejected(self):
        x=copy.deepcopy(BASE);x['wiki']='http://en.wikipedia.org/wiki/X'
        with self.assertRaises(ValueError):audit(raw(x))
    def test_fake_subdomain(self):
        x=copy.deepcopy(BASE);x['arxiv']='https://arxiv.org.evil.com/abs/X'
        with self.assertRaises(ValueError):audit(raw(x))
    def test_arxiv_search_not_abs(self):
        x=copy.deepcopy(BASE);x['arxiv']='https://arxiv.org/search/?q=X'
        with self.assertRaises(ValueError):audit(raw(x))
    def test_wiki_not_article(self):
        x=copy.deepcopy(BASE);x['wiki']='https://en.wikipedia.org/w/api.php'
        with self.assertRaises(ValueError):audit(raw(x))
    def test_username_spoof(self):
        x=copy.deepcopy(BASE);x['wiki']='https://en.wikipedia.org@evil.com/wiki/X'
        with self.assertRaises(ValueError):audit(raw(x))
    def test_equal_dates(self):
        x=copy.deepcopy(BASE);x['arxiv_pub']=x['wiki_rev']
        with self.assertRaises(ValueError):audit(raw(x))
    def test_reverse_dates(self):
        x=copy.deepcopy(BASE);x['arxiv_pub']='2020-01-01T00:00:00Z'
        with self.assertRaises(ValueError):audit(raw(x))
    def test_verdict(self):
        x=copy.deepcopy(BASE);x['verdict']='OLD'
        with self.assertRaises(ValueError):audit(raw(x))
    def test_naive_time(self):
        x=copy.deepcopy(BASE);x['read']='2026-06-01T01:00:00'
        with self.assertRaises(ValueError):audit(raw(x))
    def test_non_dict(self):
        with self.assertRaises(ValueError):audit(b'[]\n')
    def test_bad_commit(self):
        with self.assertRaises(ValueError):observe(raw(),commit='main',registry=REG)
    def test_unregistered(self):
        with self.assertRaises(ValueError):observe(raw(),commit=COMMIT,registry={'agents':[{'name':'jane'}]})
    def test_observation_no_decision(self):
        o=observe(raw(),commit=COMMIT,registry=REG)
        self.assertEqual(o['observation_status'],'AUDITED_SOURCE_RECORDS')
        self.assertIsNone(o['collective_choice'])
        self.assertIsNone(o['agent_proposal'])
        self.assertFalse(o['action_executed'])
    def test_no_runtime_attestation(self):self.assertFalse(observe(raw(),commit=COMMIT)['independent_runtime_attestation'])
    def test_last_read(self):self.assertEqual(audit(raw())['last_read'],BASE['read'])
    def test_port(self):
        x=copy.deepcopy(BASE);x['wiki']='https://en.wikipedia.org:443/wiki/X'
        with self.assertRaises(ValueError):audit(raw(x))
    def test_bad_json_unicode(self):
        with self.assertRaises(ValueError):audit(b'\xff\n')
if __name__=='__main__': unittest.main()
