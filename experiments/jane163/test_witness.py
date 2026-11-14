import copy
import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from witness import Auditor,Root,checkpoint,envelope,scheduler_records,validate_scheduler,key_hex,sign,verify,demo,sha

class TestWitness(unittest.TestCase):
    def setUp(self):
        self.records=scheduler_records(6)
        self.keys=[Ed25519PrivateKey.generate() for _ in range(3)]
        self.roots={f'r{i}':Root(key_hex(self.keys[i]),f'a{i}') for i in range(3)}
        self.a=Auditor(':memory:',self.roots,6)
    def tearDown(self):self.a.close()
    def claim(self,i,start=1,end=6,nonce=None):
        return envelope(self.keys[i],checkpoint(self.records,start,end,f'r{i}',f'a{i}',nonce or f'n{i}'))
    def valid(self):return [self.claim(i) for i in range(3)]
    def test_positive(self):self.assertEqual(self.a.audit(self.valid(),self.records)['status'],'MATCHED_FIXTURE_CUSTODY')
    def test_number_accepted(self):self.assertEqual(self.a.audit(self.valid())['accepted'],3)
    def test_ledger(self):self.a.audit(self.valid());self.assertEqual(self.a.chain_status(),'VALID_LOCAL_CHAIN')
    def test_two_roots(self):self.assertEqual(self.a.audit(self.valid()[:2])['status'],'INSUFFICIENT_DECLARED_CUSTODY')
    def test_same_admin(self):
        self.a.roots['r1']=Root(key_hex(self.keys[1]),'a0')
        b=self.valid();b[1]['body']['admin']='a0';b[1]['signature']=sign(self.keys[1],b[1]['body'])
        self.assertEqual(self.a.audit(b)['claimed_independent_admins'],2)
    def test_tamper_signature(self):
        b=self.valid();b[0]['body']['end_head']='1'*64
        self.assertIn('BAD_SIGNATURE_OR_UNKNOWN_ROOT',self.a.audit(b)['rejected'])
    def test_bad_key(self):
        b=self.valid();b[0]['signature']=sign(self.keys[1],b[0]['body'])
        self.assertIn('BAD_SIGNATURE_OR_UNKNOWN_ROOT',self.a.audit(b)['rejected'])
    def test_unknown_root(self):
        b=self.valid();b[0]['body']['root']='unknown';self.assertEqual(self.a.audit(b)['accepted'],2)
    def test_replay_in_batch(self):
        b=self.valid();b.append(copy.deepcopy(b[0]));self.assertIn('REPLAY',self.a.audit(b)['rejected'])
    def test_bad_admin(self):
        b=self.valid();b[0]['body']['admin']='fake';b[0]['signature']=sign(self.keys[0],b[0]['body'])
        self.assertIn('INVALID_CLAIM',self.a.audit(b)['rejected'])
    def test_missing_range(self):
        b=[self.claim(0,1,2),self.claim(1,4,6),self.claim(2,4,6)]
        self.assertEqual(self.a.audit(b)['missing_sequences'],[3])
    def test_suppression_status(self):
        b=[self.claim(0,1,2),self.claim(1,4,6),self.claim(2,4,6)]
        self.assertEqual(self.a.audit(b)['status'],'SELECTIVE_SUPPRESSION')
    def test_suffix_truncation(self):
        b=[self.claim(i,1,4) for i in range(3)]
        self.assertEqual(self.a.audit(b)['status'],'TRUNCATED_OR_MISSING_RANGE')
    def test_suffix_flag(self):
        b=[self.claim(i,1,4) for i in range(3)]
        self.assertTrue(self.a.audit(b)['suffix_truncation'])
    def test_conflict_same_range(self):
        b=self.valid();b[2]['body']['end_head']='f'*64;b[2]['signature']=sign(self.keys[2],b[2]['body'])
        self.assertEqual(self.a.audit(b)['status'],'CONFLICTING_COMMITMENTS')
    def test_conflict_end(self):
        b=[self.claim(0,1,6),self.claim(1,2,6)]
        b[1]['body']['end_head']='c'*64;b[1]['signature']=sign(self.keys[1],b[1]['body'])
        self.assertTrue(any(x['kind']=='CONFLICTING_END' for x in self.a.audit(b)['conflicts']))
    def test_broken_link(self):
        b=[self.claim(0,1,3),self.claim(1,4,6)]
        b[1]['body']['previous_head']='c'*64;b[1]['signature']=sign(self.keys[1],b[1]['body'])
        self.assertTrue(any(x['kind']=='BROKEN_RANGE_LINK' for x in self.a.audit(b)['conflicts']))
    def test_local_log_mismatch(self):
        b=self.valid();b[0]['body']['end_head']='1'*64;b[0]['signature']=sign(self.keys[0],b[0]['body'])
        self.assertTrue(self.a.audit(b,self.records)['local_log_mismatches'])
    def test_bad_scheduler(self):
        bad=copy.deepcopy(self.records);bad[1]['selected']='C'
        self.assertIn('INVALID_LOCAL_SCHEDULER',self.a.audit(self.valid(),bad)['rejected'])
    def test_valid_scheduler(self):self.assertTrue(validate_scheduler(self.records))
    def test_scheduler_tampered(self):
        bad=copy.deepcopy(self.records);bad[2]['selected']='Z';self.assertFalse(validate_scheduler(bad))
    def test_scheduler_reordered(self):self.assertFalse(validate_scheduler(self.records[::-1]))
    def test_scheduler_empty(self):self.assertTrue(validate_scheduler([]))
    def test_range_bad_start(self):
        with self.assertRaises(ValueError):checkpoint(self.records,0,3,'x','y','z')
    def test_range_bad_end(self):
        with self.assertRaises(ValueError):checkpoint(self.records,1,7,'x','y','z')
    def test_range_inverted(self):
        with self.assertRaises(ValueError):checkpoint(self.records,4,3,'x','y','z')
    def test_signature(self):
        claim=self.claim(0);self.assertTrue(verify(self.roots['r0'].key,claim['body'],claim['signature']))
    def test_signature_corrupt(self):
        claim=self.claim(0);self.assertFalse(verify(self.roots['r0'].key,claim['body'],'bad'))
    def test_signature_no_claims(self):self.assertEqual(self.a.audit([])['status'],'TRUNCATED_OR_MISSING_RANGE')
    def test_sha_length(self):self.assertEqual(len(sha({'a':1})),64)
    def test_original_parent_unchanged(self):self.assertEqual(self.a.audit(self.valid())['active_parent'],'FROZEN')
    def test_no_jane_learning(self):self.assertFalse(self.a.audit(self.valid())['jane_learning_applied'])
    def test_no_verified_independence(self):self.assertFalse(self.a.audit(self.valid())['real_independence_verified'])
    def test_non_identical_key_roots(self):self.assertEqual(len({key_hex(k) for k in self.keys}),3)
    def test_no_false_quorum_shared_admin(self):
        self.a.roots={f'r{i}':Root(key_hex(self.keys[i]),'same') for i in range(3)}
        b=[envelope(self.keys[i],checkpoint(self.records,1,6,f'r{i}','same',f'n{i}')) for i in range(3)]
        self.assertEqual(self.a.audit(b)['status'],'INSUFFICIENT_DECLARED_CUSTODY')
    def test_external_head_mismatch(self):self.assertEqual(self.a.chain_status('a'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_local_tampering(self):
        self.a.audit(self.valid());self.a.db.execute("UPDATE observations SET payload='{}' WHERE id=1");self.a.db.commit()
        self.assertEqual(self.a.chain_status(),'LOCAL_TAMPER')
    def test_restart_readable(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'db.sqlite';a=Auditor(p,self.roots,6);a.audit(self.valid());head=a.db.execute('SELECT head FROM observations').fetchone()[0];a.close()
            b=Auditor(p,self.roots,6);self.assertEqual(b.chain_status(head),'VALID_LOCAL_CHAIN');b.close()
    def test_no_external_truncation_proof(self):self.assertEqual(self.a.chain_status(),'VALID_LOCAL_CHAIN')
    def test_case_result(self):self.assertEqual(demo()['matched']['status'],'MATCHED_FIXTURE_CUSTODY')
    def test_case_truncation(self):self.assertEqual(demo()['suffix_truncated']['status'],'TRUNCATED_OR_MISSING_RANGE')
    def test_claim_end_head(self):self.assertEqual(self.claim(0)['body']['end_head'],self.records[-1]['head'])
    def test_claim_previous_head(self):self.assertEqual(self.claim(0,3,5)['body']['previous_head'],self.records[1]['head'])
    def test_duplicate_nonce_separate_roots(self):
        b=[self.claim(i,nonce='same') for i in range(3)]
        self.assertEqual(self.a.audit(b)['accepted'],3)
    def test_invalid_protocol(self):
        b=self.valid();b[0]['body']['protocol']='OTHER';b[0]['signature']=sign(self.keys[0],b[0]['body'])
        self.assertIn('INVALID_CLAIM',self.a.audit(b)['rejected'])
if __name__=='__main__':unittest.main(verbosity=2)
