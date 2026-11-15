import unittest
from copy import deepcopy
from run_attestation import verify,sha,canon,fetch_github
class VerifyTest(unittest.TestCase):
    def setUp(self):
        self.head='a'*40
        self.receipt={'schema':'jane.runtime-receipt/1','verdict':'OBSERVED_ALLOWLISTED_PROCESS_RUN',
          'runner_claims':{'github_repository':'DavidWise01/jane','github_sha':self.head,
            'github_run_id':'12345','github_workflow_ref':'DavidWise01/jane/.github/workflows/jane226-runtime.yml@refs/heads/main'},
          'collective_decision':'UNRESOLVED','action_executed':False}
        self.sign()
        self.run={'id':12345,'head_sha':self.head,'event':'workflow_dispatch','status':'completed',
                  'conclusion':'success','run_attempt':1,'path':'.github/workflows/jane226-runtime.yml',
                  'head_branch':'main','repository':{'full_name':'DavidWise01/jane'},
                  'head_repository':{'full_name':'DavidWise01/jane'},
                  'actor':{'login':'DavidWise01'},'triggering_actor':{'login':'DavidWise01'}}
        self.commit={'sha':self.head}
        self.job={'id':44,'run_id':12345,'head_sha':self.head,'status':'completed','conclusion':'success',
                  'steps':[{'name':'Run one bounded local process','conclusion':'success'}]}
        self.artifact={'id':55,'workflow_run':{'id':12345},'name':'jane226-runtime-receipt','expired':False}
    def sign(self):
        self.receipt['receipt_sha256']=sha(canon({k:v for k,v in self.receipt.items() if k not in ('verdict','receipt_sha256')}))
    def audit(self): return verify(self.receipt,self.run,self.commit,self.job,self.artifact)['verdict']
    def test_valid(self): self.assertEqual(self.audit(),'GITHUB_METADATA_AND_JOB_CORROBORATED')
    def test_valid_does_not_claim_hardware(self): self.assertEqual(verify(self.receipt,self.run,self.commit,self.job,self.artifact)['runner_attestation'],'GITHUB_PLATFORM_RECORD_CORROBORATED_ONLY')
    def test_valid_never_authorizes(self):
        r=verify(self.receipt,self.run,self.commit,self.job,self.artifact)
        self.assertEqual(r['collective_decision'],'UNRESOLVED');self.assertFalse(r['action_executed'])
    def test_missing_remote(self): self.assertEqual(verify(self.receipt)['verdict'],'NO_INDEPENDENT_REMOTE_METADATA')
    def test_missing_commit(self): self.assertEqual(verify(self.receipt,self.run)['verdict'],'NO_INDEPENDENT_REMOTE_METADATA')
    def test_missing_job(self): self.assertEqual(verify(self.receipt,self.run,self.commit)['verdict'],'NO_INDEPENDENT_JOB_EVIDENCE')
    def test_missing_artifact(self): self.assertEqual(verify(self.receipt,self.run,self.commit,self.job)['verdict'],'NO_INDEPENDENT_ARTIFACT_EVIDENCE')
    def test_local_false(self): self.receipt['verdict']='WITHHELD';self.assertEqual(self.audit(),'LOCAL_EXECUTION_NOT_VERIFIED')
    def test_bad_receipt(self): self.assertEqual(verify(None)['verdict'],'BAD_RECEIPT')
    def test_tamper(self):self.receipt['action_executed']=True;self.assertEqual(self.audit(),'LOCAL_RECEIPT_DIGEST_MISMATCH')
    def test_bad_hash(self):self.receipt['receipt_sha256']='bad';self.assertEqual(self.audit(),'BAD_RECEIPT_DIGEST')
    def test_no_claims(self):self.receipt.pop('runner_claims');self.sign();self.assertEqual(self.audit(),'NO_RUNNER_CLAIMS')
    def test_wrong_repo(self):self.receipt['runner_claims']['github_repository']='other/repo';self.sign();self.assertEqual(self.audit(),'INVALID_RUNNER_IDENTITY_CLAIM')
    def test_bad_sha(self):self.receipt['runner_claims']['github_sha']='bad';self.sign();self.assertEqual(self.audit(),'INVALID_RUNNER_IDENTITY_CLAIM')
    def test_bad_run_id(self):self.receipt['runner_claims']['github_run_id']='123/../../';self.sign();self.assertEqual(self.audit(),'INVALID_RUNNER_IDENTITY_CLAIM')
    def test_wrong_workflow(self):self.receipt['runner_claims']['github_workflow_ref']='x';self.sign();self.assertEqual(self.audit(),'INVALID_RUNNER_IDENTITY_CLAIM')
    def test_wrong_run(self):self.run['id']=1;self.assertEqual(self.audit(),'RUN_ID_OR_COMMIT_MISMATCH')
    def test_wrong_run_commit(self):self.run['head_sha']='b'*40;self.assertEqual(self.audit(),'RUN_ID_OR_COMMIT_MISMATCH')
    def test_bad_event(self):self.run['event']='push';self.assertEqual(self.audit(),'RUN_NOT_SUCCESSFUL_FIRST_ATTEMPT')
    def test_pending(self):self.run['status']='in_progress';self.assertEqual(self.audit(),'RUN_NOT_SUCCESSFUL_FIRST_ATTEMPT')
    def test_failed(self):self.run['conclusion']='failure';self.assertEqual(self.audit(),'RUN_NOT_SUCCESSFUL_FIRST_ATTEMPT')
    def test_rerun(self):self.run['run_attempt']=2;self.assertEqual(self.audit(),'RUN_NOT_SUCCESSFUL_FIRST_ATTEMPT')
    def test_wrong_path(self):self.run['path']='other';self.assertEqual(self.audit(),'WRONG_WORKFLOW_OR_BRANCH')
    def test_wrong_branch(self):self.run['head_branch']='dev';self.assertEqual(self.audit(),'WRONG_WORKFLOW_OR_BRANCH')
    def test_wrong_repository(self):self.run['repository']['full_name']='other';self.assertEqual(self.audit(),'WRONG_REMOTE_REPOSITORY')
    def test_wrong_head_repo(self):self.run['head_repository']['full_name']='other';self.assertEqual(self.audit(),'WRONG_REMOTE_REPOSITORY')
    def test_actor(self):self.run['actor']['login']='other';self.assertEqual(self.audit(),'UNAUTHORIZED_ACTOR')
    def test_trigger_actor(self):self.run['triggering_actor']['login']='other';self.assertEqual(self.audit(),'UNAUTHORIZED_ACTOR')
    def test_commit(self):self.commit['sha']='b'*40;self.assertEqual(self.audit(),'REMOTE_COMMIT_MISMATCH')
    def test_job_run(self):self.job['run_id']=44;self.assertEqual(self.audit(),'JOB_EXECUTION_NOT_CORROBORATED')
    def test_job_head(self):self.job['head_sha']='b'*40;self.assertEqual(self.audit(),'JOB_EXECUTION_NOT_CORROBORATED')
    def test_job_conclusion(self):self.job['conclusion']='failure';self.assertEqual(self.audit(),'JOB_EXECUTION_NOT_CORROBORATED')
    def test_job_step(self):self.job['steps'][0]['conclusion']='skipped';self.assertEqual(self.audit(),'JOB_EXECUTION_NOT_CORROBORATED')
    def test_artifact_id(self):self.artifact['workflow_run']['id']=44;self.assertEqual(self.audit(),'ARTIFACT_NOT_CORROBORATED')
    def test_artifact_name(self):self.artifact['name']='bad';self.assertEqual(self.audit(),'ARTIFACT_NOT_CORROBORATED')
    def test_expired(self):self.artifact['expired']=True;self.assertEqual(self.audit(),'ARTIFACT_NOT_CORROBORATED')
    def test_missing_schema(self):self.receipt['schema']='other';self.assertEqual(self.audit(),'LOCAL_EXECUTION_NOT_VERIFIED')
if __name__=='__main__':unittest.main()