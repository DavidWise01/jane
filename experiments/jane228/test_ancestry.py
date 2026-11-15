import copy
import hashlib
import unittest
from ancestry import verify,validate,digest,TRUST_FIELDS

def node(i,kind='github_actions'):
    roots={k:f'{k}-{i}' for k in TRUST_FIELDS}
    if kind=='github_actions':roots['platform_root']='github.com/actions'
    return dict(id=f'agent{i}',kind=kind,repo=f'owner/repo{i}',run_id=str(100+i),
                commit=f'commit{i}',evidence_digest=hashlib.sha256(str(i).encode()).hexdigest(),
                evidence_origin='separately_retrieved',roots=roots)

class Lineage(unittest.TestCase):
    def test_empty(self):self.assertEqual(verify([])['verdict'],'NO_EXECUTION_WITNESSES')
    def test_nonlist(self):self.assertEqual(verify({})['verdict'],'BAD_WITNESS_SET')
    def test_limit(self):self.assertEqual(verify([{}]*101)['verdict'],'BAD_WITNESS_SET')
    def test_one(self):self.assertEqual(verify([node(1)])['verdict'],'SINGLE_EXECUTION_WITNESS')
    def test_two_github(self):
        r=verify([node(1),node(2)])
        self.assertEqual(r['verdict'],'SHARED_EXECUTION_ANCESTRY')
        self.assertEqual(r['collisions'][0]['shared'],['platform_root'])
    def test_three_github_one_cluster(self):
        r=verify([node(i) for i in range(3)])
        self.assertEqual(r['components'],[['agent0','agent1','agent2']])
    def test_distinct_declared_roots_no_attestation(self):
        r=verify([node(1,'external_attestor'),node(2,'local_subprocess')])
        self.assertEqual(r['verdict'],'DECLARED_DISTINCT_ROOTS_NOT_ATTESTED')
        self.assertEqual(r['independent_execution_witnesses_established'],0)
    def test_missing_root(self):
        a,b=node(1,'external_attestor'),node(2,'external_attestor');b['roots']['operator_root']=None
        self.assertEqual(verify([a,b])['verdict'],'UNKNOWN_EXECUTION_ANCESTRY')
    def test_collision_takes_priority_over_unknown(self):
        a,b=node(1,'external_attestor'),node(2,'external_attestor');b['roots']['operator_root']=None;b['roots']['runner_root']=a['roots']['runner_root']
        self.assertEqual(verify([a,b])['verdict'],'SHARED_EXECUTION_ANCESTRY')
    def test_same_run(self):
        a,b=node(1,'external_attestor'),node(2,'external_attestor');b['repo']=a['repo'];b['run_id']=a['run_id']
        self.assertIn('same_run',verify([a,b])['collisions'][0]['shared'])
    def test_same_evidence(self):
        a,b=node(1,'external_attestor'),node(2,'external_attestor');b['evidence_digest']=a['evidence_digest']
        self.assertIn('same_evidence_digest',verify([a,b])['collisions'][0]['shared'])
    def test_shared_credential(self):
        a,b=node(1,'external_attestor'),node(2,'external_attestor');b['roots']['credential_root']=a['roots']['credential_root']
        self.assertIn('credential_root',verify([a,b])['collisions'][0]['shared'])
    def test_shared_workflow(self):
        a,b=node(1,'external_attestor'),node(2,'external_attestor');b['roots']['workflow_root']=a['roots']['workflow_root']
        self.assertIn('workflow_root',verify([a,b])['collisions'][0]['shared'])
    def test_transitive_cluster(self):
        a,b,c=[node(i,'external_attestor') for i in range(3)];b['roots']['runner_root']=a['roots']['runner_root'];c['roots']['operator_root']=b['roots']['operator_root']
        r=verify([a,b,c]);self.assertEqual(r['components'],[['agent0','agent1','agent2']])
    def test_two_clusters(self):
        a,b,c,d=[node(i,'external_attestor') for i in range(4)];b['roots']['runner_root']=a['roots']['runner_root'];d['roots']['runner_root']=c['roots']['runner_root']
        self.assertEqual(verify([a,b,c,d])['components'],[['agent0','agent1'],['agent2','agent3']])
    def test_duplicate_id(self):
        a,b=node(1),node(2);b['id']=a['id'];self.assertEqual(verify([a,b])['verdict'],'DUPLICATE_WITNESS_ID')
    def test_bad_record(self):self.assertEqual(verify(['not a record'])['verdict'],'BAD_RECORD')
    def test_missing_field(self):
        a=node(1);del a['roots'];self.assertEqual(verify([a])['verdict'],'MISSING_FIELDS')
    def test_bad_kind(self):
        a=node(1);a['kind']='cloud';self.assertEqual(verify([a])['verdict'],'BAD_KIND')
    def test_bad_id(self):
        a=node(1);a['id']='../../who';self.assertEqual(verify([a])['verdict'],'BAD_IDENTIFIER')
    def test_invalid_commit(self):
        a=node(1);a['commit']=[];self.assertEqual(verify([a])['verdict'],'BAD_IDENTIFIER')
    def test_bad_digest(self):
        a=node(1);a['evidence_digest']='abc';self.assertEqual(verify([a])['verdict'],'BAD_EVIDENCE_DIGEST')
    def test_bad_origin(self):
        a=node(1);a['evidence_origin']='pretend';self.assertEqual(verify([a])['verdict'],'BAD_ORIGIN')
    def test_root_missing_key(self):
        a=node(1);a['roots'].pop('source_root');self.assertEqual(verify([a])['verdict'],'BAD_ROOT_SCHEMA')
    def test_root_extra_key(self):
        a=node(1);a['roots']['fake_root']='x';self.assertEqual(verify([a])['verdict'],'BAD_ROOT_SCHEMA')
    def test_bad_root_value(self):
        a=node(1);a['roots']['runner_root']={};self.assertEqual(verify([a])['verdict'],'BAD_ROOT_VALUE')
    def test_forged_github_root(self):
        a=node(1);a['roots']['platform_root']='aws';self.assertEqual(verify([a])['verdict'],'FORGED_PLATFORM_ROOT')
    def test_self_reported_flag(self):
        a=node(1);a['evidence_origin']='self_reported';self.assertIn('Self-reported',verify([a])['notes'][1])
    def test_sorted_output(self):
        a,b=node(5),node(2);self.assertEqual(verify([a,b])['components'],[['agent2','agent5']])
    def test_hardware_not_proven(self):
        self.assertFalse(verify([node(1),node(2)])['verified_physical_or_hardware_independence'])
    def test_no_jane_choice(self):
        self.assertEqual(verify([node(1)])['jane_collective_decision'],'UNRESOLVED')
    def test_no_action(self):self.assertFalse(verify([node(1)])['action_executed'])
    def test_digest_valid(self):
        r=verify([node(1)]);x={k:v for k,v in r.items() if k!='result_sha256'};self.assertEqual(r['result_sha256'],digest(x))
    def test_digest_mutation(self):
        r=verify([node(1)]);r['witnesses_examined']=5;self.assertNotEqual(r['result_sha256'],digest({k:v for k,v in r.items() if k!='result_sha256'}))
    def test_no_implicit_three_witness(self):
        self.assertEqual(verify([node(0),node(1),node(2)])['independent_execution_witnesses_established'],0)
    def test_independence_unknown_not_approved(self):
        a,b=node(1,'external_attestor'),node(2,'external_attestor');a['roots']['platform_root']=None
        self.assertEqual(verify([a,b])['independent_execution_witnesses_established'],0)

if __name__=='__main__':unittest.main()
