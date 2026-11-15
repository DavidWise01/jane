"""JANE 227 — GitHub runner metadata corroboration, not hardware attestation.

A local receipt's runner_claims never count as independent evidence. The verifier
compares them to a separately acquired GitHub Actions REST run record and commit;
without that record it withholds a remote-run conclusion.
"""
import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCHEMA='jane.github-run-crosscheck/1'
WORKFLOW='.github/workflows/jane226-runtime.yml'
REPO='DavidWise01/jane'
SHA40=re.compile(r'^[0-9a-f]{40}$')
SHA64=re.compile(r'^[0-9a-f]{64}$')
RUN_ID=re.compile(r'^[1-9][0-9]{0,18}$')

def canon(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def fetch_github(url,token=None):
    p=urllib.parse.urlsplit(url)
    if (p.scheme!='https' or p.hostname!='api.github.com' or p.port is not None
            or p.username or p.password or p.query or p.fragment
            or not p.path.startswith('/repos/DavidWise01/jane/')):
        raise ValueError('UNTRUSTED_REMOTE_LOCATION')
    headers={'Accept':'application/vnd.github+json','User-Agent':'Jane227-audit/1',
             'X-GitHub-Api-Version':'2022-11-28'}
    if token: headers['Authorization']='Bearer '+token
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=12) as resp:
        if resp.geturl()!=url: raise ValueError('GITHUB_REDIRECT_NOT_ALLOWED')
        if resp.status!=200: raise ValueError('REMOTE_HTTP_ERROR')
        data=resp.read(200_001)
        if len(data)>200_000: raise ValueError('REMOTE_TOO_LARGE')
    return json.loads(data)

def fail(code,receipt=None,metadata=None,details=None):
    out={'schema':SCHEMA,'verdict':code,'runner_attestation':'NOT_ESTABLISHED',
         'collective_decision':'UNRESOLVED','action_executed':False,
         'evidence_scope':'GITHUB_API_METADATA_CORROBORATION_NOT_HARDWARE_OR_PROCESS_ATTESTATION'}
    if receipt and isinstance(receipt,dict):
        out['local_receipt_sha256']=sha(canon(receipt))
    if metadata and isinstance(metadata,dict):
        out['remote_run_record_sha256']=sha(canon(metadata))
    if details: out['details']=details
    return out

def verify(receipt,run=None,commit=None,job=None,artifact=None):
    """All remote records MUST come from a separate trusted fetch, not the receipt."""
    if not isinstance(receipt,dict): return fail('BAD_RECEIPT')
    if receipt.get('schema')!='jane.runtime-receipt/1' or receipt.get('verdict')!='OBSERVED_ALLOWLISTED_PROCESS_RUN':
        return fail('LOCAL_EXECUTION_NOT_VERIFIED',receipt)
    claims=receipt.get('runner_claims')
    if not isinstance(claims,dict): return fail('NO_RUNNER_CLAIMS',receipt)
    if not SHA64.fullmatch(str(receipt.get('receipt_sha256',''))): return fail('BAD_RECEIPT_DIGEST',receipt)
    rbody={k:v for k,v in receipt.items() if k not in ('verdict','receipt_sha256')}
    if sha(canon(rbody)) != receipt['receipt_sha256']:
        return fail('LOCAL_RECEIPT_DIGEST_MISMATCH',receipt)
    repo=claims.get('github_repository')
    head=claims.get('github_sha')
    run_id=str(claims.get('github_run_id',''))
    workflow=claims.get('github_workflow_ref')
    if repo!=REPO or not SHA40.fullmatch(str(head)) or not RUN_ID.fullmatch(run_id) or workflow!=f'{REPO}/{WORKFLOW}@refs/heads/main':
        return fail('INVALID_RUNNER_IDENTITY_CLAIM',receipt)
    if run is None or commit is None:
        return fail('NO_INDEPENDENT_REMOTE_METADATA',receipt)
    if not isinstance(run,dict) or not isinstance(commit,dict): return fail('MALFORMED_REMOTE_METADATA',receipt)
    if str(run.get('id'))!=run_id or run.get('head_sha')!=head:
        return fail('RUN_ID_OR_COMMIT_MISMATCH',receipt,run)
    if (run.get('event')!='workflow_dispatch' or run.get('status')!='completed' or
            run.get('conclusion')!='success' or run.get('run_attempt')!=1):
        return fail('RUN_NOT_SUCCESSFUL_FIRST_ATTEMPT',receipt,run)
    if run.get('path') != WORKFLOW or run.get('head_branch')!='main':
        return fail('WRONG_WORKFLOW_OR_BRANCH',receipt,run)
    if run.get('repository',{}).get('full_name')!=REPO or run.get('head_repository',{}).get('full_name')!=REPO:
        return fail('WRONG_REMOTE_REPOSITORY',receipt,run)
    if run.get('actor',{}).get('login')!='DavidWise01' or run.get('triggering_actor',{}).get('login')!='DavidWise01':
        return fail('UNAUTHORIZED_ACTOR',receipt,run)
    if commit.get('sha')!=head or not SHA40.fullmatch(str(commit.get('sha',''))):
        return fail('REMOTE_COMMIT_MISMATCH',receipt,run)
    if not isinstance(job,dict): return fail('NO_INDEPENDENT_JOB_EVIDENCE',receipt,run)
    if (job.get('run_id')!=run['id'] or job.get('head_sha')!=head or
            job.get('status')!='completed' or job.get('conclusion')!='success' or
            not isinstance(job.get('steps'),list) or not any(s.get('name')=='Run one bounded local process' and s.get('conclusion')=='success' for s in job['steps'])):
        return fail('JOB_EXECUTION_NOT_CORROBORATED',receipt,run)
    if not isinstance(artifact,dict): return fail('NO_INDEPENDENT_ARTIFACT_EVIDENCE',receipt,run)
    if (artifact.get('workflow_run',{}).get('id')!=run['id'] or
            artifact.get('name')!='jane226-runtime-receipt' or artifact.get('expired') is not False):
        return fail('ARTIFACT_NOT_CORROBORATED',receipt,run)
    out=fail('GITHUB_METADATA_AND_JOB_CORROBORATED',receipt,run,
             details={'run_id':run['id'],'source_commit':head,
                      'job_id':job.get('id'),'artifact_id':artifact.get('id'),
                      'notice':'Does not cryptographically bind artifact bytes to local receipt; does not attest physical runner.'})
    out['runner_attestation']='GITHUB_PLATFORM_RECORD_CORROBORATED_ONLY'
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--receipt',required=True)
    ap.add_argument('--run-json')
    ap.add_argument('--commit-json')
    ap.add_argument('--job-json')
    ap.add_argument('--artifact-json')
    ap.add_argument('--out',default='crosscheck-result.json')
    args=ap.parse_args()
    receipt=json.loads(Path(args.receipt).read_text())
    def load(p): return json.loads(Path(p).read_text()) if p else None
    result=verify(receipt,load(args.run_json),load(args.commit_json),load(args.job_json),load(args.artifact_json))
    Path(args.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(result['verdict'])
    return 0 if result['verdict']=='GITHUB_METADATA_AND_JOB_CORROBORATED' else 2
if __name__=='__main__': raise SystemExit(main())