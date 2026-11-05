'use strict';
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const {build}=require('./jane-b168-proof-proposal.cjs');
const {bind}=require('./jane-b171-triple-evidence.cjs');
const {integrate}=require('./jane-b172-controlled-integration.cjs');
const {planTree,decodeBlob,readPinned,applySnapshot,gitBlob,safeName}=require('./jane-b173-pinned-tree.cjs');
const repo={full_name:'DavidWise01/jane',default_branch:'main',private:false,visibility:'public',archived:false,disabled:false,fork:false};
const policy={schema:'FORMIC-REPO-POLICY-v1',enabled:true,allowed_repairs:['BUG_REPORT_TEMPLATE'],max_open_pull_requests:1};
const b167={repository:repo.full_name,status:'POLICY_EVIDENCE_PRESENT',mayCreatePR:false,mayRetry:false,mayMerge:false};
const sha='a'.repeat(40),treeSha='b'.repeat(40);
const proof=build({repo,policy,b167,baseSha:sha});
const base={schema:'JANE-B169-DRIFT-AND-CI-v1',repository:repo.full_name,proposalSha256:proof.sha256,baseSha:sha,observedSha:sha,
 status:'BASE_OBSERVED_PASS_NOT_PROPOSAL_VALIDATED',proposalChecksExecuted:false,proposalChecksPassed:false,
 mayCreatePR:false,mayMerge:false,mayRetry:false};
const local={schema:'JANE-B170-ISOLATED-REPAIR-EVALUATION-v1',status:'LOCAL_CHECKS_PASS',
 repository:repo.full_name,proposalSha256:proof.sha256,baseSha:sha,localChecksPassed:true,workspaceDeleted:true,
 proposalTestsExecuted:true,githubCiObserved:false,githubCiPassed:false,repositoryCodeExecuted:false,
 mayCreatePR:false,mayMerge:false,mayRetry:false,
 checks:['PATCH_BYTES','PATCH_SHA256','FIXED_TEMPLATE','ISSUE_TEMPLATE_FRONT_MATTER','REPRO_STEPS',
 'EXPECTED_AND_ACTUAL','SECRET_HYGIENE'].map(name=>({name,status:'PASS'}))};
const t='2026-11-05T20:00:00Z';
const triple=bind({proof,base,local,baseObservedAt:t,localEvaluatedAt:t,nowIso:t});
assert.equal(triple.status,'EVIDENCE_BOUND_NO_EXECUTION');
const scratch=integrate({proposal:proof,base,local,triple});
assert.equal(scratch.status,'SCRATCH_GIT_PATCH_PASS');
const content=Buffer.from('# test repository\n','utf8'),blobSha=gitBlob(content);
const plan={tree:[{path:'README.md',type:'blob',mode:'100644',sha:blobSha,size:content.length}],truncated:false};
assert.equal(planTree(plan).status,'SNAPSHOT_PLAN');
assert.equal(planTree({...plan,truncated:true}).status,'HOLD');
assert.equal(planTree({tree:[{...plan.tree[0],path:'../escape'}],truncated:false}).status,'HOLD');
assert.equal(planTree({tree:[{...plan.tree[0],mode:'120000'}],truncated:false}).status,'HOLD');
assert.equal(planTree({tree:[{...plan.tree[0],path:'.github/ISSUE_TEMPLATE/bug_report.md'}],truncated:false}).status,'HOLD');
assert.equal(safeName('dir/../../bad'),false);
const blob={encoding:'base64',content:content.toString('base64'),sha:blobSha,size:content.length};
assert.deepEqual(decodeBlob(blob,plan.tree[0]),content);
assert.throws(()=>decodeBlob({...blob,sha:'f'.repeat(40)},plan.tree[0]),/BLOB_MISMATCH/);
const prefix='/repos/DavidWise01/jane',ref=prefix+'/git/ref/heads/main';
const fetchFn=async route=>{
 if(route===prefix)return{full_name:repo.full_name,owner:{login:'DavidWise01'},private:false,default_branch:'main',archived:false,disabled:false,fork:false};
 if(route===ref)return{object:{sha}};
 if(route===prefix+'/git/commits/'+sha)return{sha,tree:{sha:treeSha}};
 if(route===prefix+'/git/trees/'+treeSha+'?recursive=1')return plan;
 if(route===prefix+'/git/blobs/'+blobSha)return blob;
 throw Error('UNEXPECTED_ROUTE '+route);
};
(async()=>{
 const tree=await readPinned(proof,'',fetchFn);
 assert.equal(tree.files,1);
 const good=applySnapshot({proof,base,local,triple,scratch,tree});
 assert.equal(good.status,'PINNED_TREE_PATCH_PASS');
 assert.equal(good.cleanupConfirmed,true);
 assert.equal(good.sourceFilesChecked,1);
 assert.equal(good.targetRepoCiExecuted,false);
 assert.equal(good.mayCreatePR,false);
 const conflict=applySnapshot({proof,base,local,triple,scratch,tree:{...tree,blobs:[{entry:{...plan.tree[0],path:'../outside'},bytes:content}]}});
 assert.equal(conflict.status,'HOLD');
 const moved=await readPinned(proof,'',async route=>route===ref?{object:{sha:'c'.repeat(40)}}:fetchFn(route)).catch(e=>e.message);
 assert.equal(moved,'BASE_SHA_DRIFT');
 console.log('PASS B173: pinned tree, verified Git blob bytes, real scratch apply, unchanged source and cleanup, no repo CI');
})().catch(err=>{console.error(err);process.exitCode=1});
