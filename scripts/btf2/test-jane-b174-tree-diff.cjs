'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {build}=require('./jane-b168-proof-proposal.cjs');
const {bind}=require('./jane-b171-triple-evidence.cjs');
const {integrate}=require('./jane-b172-controlled-integration.cjs');
const {gitBlob}=require('./jane-b173-pinned-tree.cjs');
const {evaluate,audit,inventory,changes}=require('./jane-b174-tree-diff.cjs');
const repo={full_name:'DavidWise01/jane',default_branch:'main',private:false,visibility:'public',archived:false,disabled:false,fork:false};
const policy={schema:'FORMIC-REPO-POLICY-v1',enabled:true,allowed_repairs:['BUG_REPORT_TEMPLATE'],max_open_pull_requests:1};
const b167={repository:repo.full_name,status:'POLICY_EVIDENCE_PRESENT',mayCreatePR:false,mayRetry:false,mayMerge:false};
const sha='a'.repeat(40),proposal=build({repo,policy,b167,baseSha:sha});
const base={schema:'JANE-B169-DRIFT-AND-CI-v1',repository:repo.full_name,proposalSha256:proposal.sha256,
 baseSha:sha,observedSha:sha,status:'BASE_OBSERVED_PASS_NOT_PROPOSAL_VALIDATED',
 proposalChecksExecuted:false,proposalChecksPassed:false,mayCreatePR:false,mayRetry:false,mayMerge:false};
const local={schema:'JANE-B170-ISOLATED-REPAIR-EVALUATION-v1',repository:repo.full_name,
 proposalSha256:proposal.sha256,baseSha:sha,status:'LOCAL_CHECKS_PASS',localChecksPassed:true,
 workspaceDeleted:true,proposalTestsExecuted:true,githubCiObserved:false,githubCiPassed:false,
 repositoryCodeExecuted:false,mayCreatePR:false,mayRetry:false,mayMerge:false,
 checks:['PATCH_BYTES','PATCH_SHA256','FIXED_TEMPLATE','ISSUE_TEMPLATE_FRONT_MATTER',
 'REPRO_STEPS','EXPECTED_AND_ACTUAL','SECRET_HYGIENE'].map(name=>({name,status:'PASS'}))};
const clock='2026-11-05T20:00:00Z';
const triple=bind({proof:proposal,base,local,baseObservedAt:clock,localEvaluatedAt:clock,nowIso:clock});
assert.equal(triple.status,'EVIDENCE_BOUND_NO_EXECUTION');
const scratch=integrate({proposal,base,local,triple});
assert.equal(scratch.status,'SCRATCH_GIT_PATCH_PASS');
const content=Buffer.from('# read-only tree\n'),entry={path:'README.md',type:'blob',mode:'100644',
 size:content.length,sha:gitBlob(content)};
const tree={repository:repo.full_name,baseSha:sha,treeSha:'b'.repeat(40),
 blobs:[{entry,bytes:content}]};
const inputs={proof:proposal,base,local,triple,scratch,tree};
const good=evaluate(inputs);
assert.equal(good.status,'EXACT_ONE_FILE_ADDITION');
assert.equal(good.temporaryWorkspaceRemoved,true);
assert.equal(good.before.length,1);assert.equal(good.after.length,2);
assert.equal(good.delta.additions.length,1);
assert.equal(good.delta.modifications.length,0);
assert.equal(good.delta.deletions.length,0);
assert.deepEqual(good.delta.preserved,['README.md']);
assert.equal(audit(good).status,'PASS');
assert.equal(good.authority.mayCreatePR,false);
const tampered=JSON.parse(JSON.stringify(good));tampered.after[0].sha256='f'.repeat(64);
assert.equal(audit(tampered).status,'HOLD');
const wrongSha=evaluate({...inputs,tree:{...tree,blobs:[{entry:{...entry,sha:'c'.repeat(40)},bytes:content}]}});
assert.equal(wrongSha.status,'HOLD');
const wrongBase=evaluate({...inputs,tree:{...tree,baseSha:'d'.repeat(40)}});
assert.equal(wrongBase.status,'HOLD');
const fakeDelta=changes([{path:'a',sha256:'a',bytes:1,gitBlob:'a',executable:false}],
  [{path:'a',sha256:'b',bytes:1,gitBlob:'a',executable:false}]);
assert.equal(fakeDelta.modifications.length,1);
const root=fs.mkdtempSync(path.join(os.tmpdir(),'b174-tree-'));
try{
 fs.writeFileSync(path.join(root,'unchanged'),'hello');
 const files=inventory(root);assert.equal(files.length,1);
 fs.writeFileSync(path.join(root,'newfile'),'new');
 assert.equal(changes(files,inventory(root)).additions.length,1);
}finally{fs.rmSync(root,{recursive:true,force:true})}
console.log('PASS B174: actual on-disk before/after Git manifest, exact delta, tamper HOLD, cleanup, no remote writes');
