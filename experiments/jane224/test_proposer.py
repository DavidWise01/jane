import json
import unittest
from proposer import propose, jsonlines, read_limited, hash_bytes

COMMIT='a'*40
W='https://en.wikipedia.org/wiki/Alpha'
A='https://arxiv.org/abs/2606.01234'

def row(w=W,a=A, rev='2024-01-01T00:00:00Z', pub='2026-01-01T00:00:00Z'):
    return dict(wiki=w, arxiv=a, wiki_rev=rev, arxiv_pub=pub,
                arxiv_title='Example', read='2026-02-01T00:00:00+00:00',verdict='NEW')

def encode(*rows):return ''.join(json.dumps(x)+'\n' for x in rows).encode()

def run(ledger=None,ground=b'',commit=COMMIT):
    return propose(encode(row()) if ledger is None else ledger,ground,nom_commit=commit)

class ProposerTests(unittest.TestCase):
    def test_empty(self):self.assertEqual(run(b'')['status'],'NO_UNGROUNDED_CITATION')
    def test_first_gap(self):self.assertEqual(run()['candidate']['wiki'],W)
    def test_candidate_is_not_jane(self):self.assertFalse(run()['jane_collective_answered'])
    def test_nom_did_not_speak(self):self.assertFalse(run()['origin_agent_spoke'])
    def test_no_collective_choice(self):self.assertIsNone(run()['collective_choice'])
    def test_no_action_authorized(self):self.assertFalse(run()['next_action_authorized'])
    def test_origin_described(self):self.assertIn('not NOM preference',run()['candidate']['origin'])
    def test_receipt_digest(self):
        x=run(); h=x.pop('receipt_sha256'); self.assertEqual(h,hash_bytes(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()))
    def test_content_address(self):self.assertEqual(run()['source']['ledger_sha256'],hash_bytes(encode(row())))
    def test_full_sha(self):
        with self.assertRaises(ValueError):run(commit='abcd')
    def test_uppercase_sha(self):
        with self.assertRaises(ValueError):run(commit='A'*40)
    def test_bad_json(self):
        with self.assertRaises(ValueError):run(b'{')
    def test_invalid_utf8(self):
        with self.assertRaises(ValueError):run(b'\xff')
    def test_non_object(self):
        with self.assertRaises(ValueError):run(b'[]\n')
    def test_bad_verdict(self):
        with self.assertRaises(ValueError):run(encode(dict(row(),verdict='OLD')))
    def test_newer_required(self):
        with self.assertRaises(ValueError):run(encode(row(pub='2023-01-01T00:00:00Z')))
    def test_naive_timestamp(self):
        with self.assertRaises(ValueError):run(encode(row(pub='2026-01-01')))
    def test_invalid_read(self):
        with self.assertRaises(ValueError):run(encode(dict(row(),read='nonsense')))
    def test_wrong_wiki_host(self):
        with self.assertRaises(ValueError):run(encode(row(w='https://fake.example/wiki/A')))
    def test_wrong_arxiv_host(self):
        with self.assertRaises(ValueError):run(encode(row(a='https://evil.test/abs/1')))
    def test_http_rejected(self):
        with self.assertRaises(ValueError):run(encode(row(w='http://en.wikipedia.org/wiki/A')))
    def test_port_rejected(self):
        with self.assertRaises(ValueError):run(encode(row(w='https://en.wikipedia.org:443/wiki/A')))
    def test_query_rejected(self):
        with self.assertRaises(ValueError):run(encode(row(w=W+'?x=y')))
    def test_frag_rejected(self):
        with self.assertRaises(ValueError):run(encode(row(a=A+'#frag')))
    def test_duplicate(self):
        with self.assertRaises(ValueError):run(encode(row(),row()))
    def test_grounded(self):self.assertEqual(run(ground=encode(dict(wiki=W,arxiv=A)))['status'],'NO_UNGROUNDED_CITATION')
    def test_ground_count(self):self.assertEqual(run(ground=encode(dict(wiki=W,arxiv=A)))['counts']['unique_grounded_pairs'],1)
    def test_rogue_ground(self):
        with self.assertRaises(ValueError):run(ground=encode(dict(wiki=W,arxiv='https://arxiv.org/abs/2607.99999')))
    def test_invalid_ground_source(self):
        with self.assertRaises(ValueError):run(ground=encode(dict(wiki='https://evil.test/a',arxiv=A)))
    def test_two_chooses_first(self):
        a=run(ledger=encode(row(),row('https://en.wikipedia.org/wiki/B','https://arxiv.org/abs/2606.56789')))
        self.assertEqual(a['candidate']['ledger_index'],1)
    def test_skips_grounded(self):
        a=run(ledger=encode(row(),row('https://en.wikipedia.org/wiki/B','https://arxiv.org/abs/2606.56789')),
              ground=encode(dict(wiki=W,arxiv=A)))
        self.assertEqual(a['candidate']['ledger_index'],2)
    def test_limit_file(self):
        import tempfile
        with tempfile.NamedTemporaryFile() as f:
            f.write(b'a'*2_000_001);f.flush()
            with self.assertRaises(ValueError):read_limited(f.name)
    def test_limit_rows(self):
        with self.assertRaises(ValueError):jsonlines(b'\n'*10_001)
    def test_no_source_mutation(self):
        data=encode(row()); before=bytes(data);run(data);self.assertEqual(before,data)
    def test_deterministic(self):self.assertEqual(run(),run())

if __name__=='__main__':unittest.main()