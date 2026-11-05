'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {build}=require('./jane-b168-proof-proposal.cjs');
const {bind}=require('./jane-b171-triple-evidence.cjs');
const {integrate}=require('./jane-b172-controlled-integration.cjs');
const {gitBlob}=require('./jane-b173-pinned-tree.cjs');
const {independentInventory,evaluate,audit,registry}=require('./jane-b176-differential-tree.cjs');
const repo={full_name:'DavidWise01/jane',default_branch:'main',private:false,visibility:'public',archived:false,disabled:false,fork:false};
const policy={schema:'FORMIC-REPO-POLICY-v1',enabled:true,allowed_repairs:['BUG_REPORT_TEMPLATE'],max_open_pull_requests:1};
const b167={repository:repo.full_name,status:'POLICY_EVIDENCE_PRESENT',mayCreatePR:false,mayRetry:false,mayMerge:false};
const sha='a'.repeat(40),proof=build({repo,policy,b167,baseSha:sha});
const base={schema:'JANE-B169-DRIFT-AND-CI-v1',repository:repo.full_name,proposalSha256:proof.sha256,
 baseSha:sha,observedSha:sha,status:'BASE_OBSERVED_PASS_NOT_PROPOSAL_VALIDATED',proposalChecksExecuted:false,proposalChecksPassed:false,
 mayCreatePR:false,mayMerge:false,mayRetry:false};
const local={schema:'JANE-B170-ISOLATED-REPAIR-EVALUATION-v1',repository:repo.full_name,proposalSha256:proof.sha256,
 baseSha:sha,status:'LOCAL_CHECKS_PASS',localChecksPassed:true,workspaceDeleted:true,proposalTestsExecuted:true,
 githubCiObserved:false,githubCiPassed:false,repositoryCodeExecuted:false,
 mayCreatePR:false,mayMerge:false,mayRetry:false,
 checks:['PATCH_BYTES','PATCH_SHA256','FIXED_TEMPLATE','ISSUE_TEMPLATE_FRONT_MATTER','REPRO_STEPS','EXPECTED_AND_ACTUAL','SECRET_HYGIENE'].map(name=>({name,status:'PASS'}))};
const when='2026-11-05T20:00:00Z',triple=bind({proof,base,local,baseObservedAt:when,localEvaluatedAt:when,nowIso:when});
const scratch=integrate({proposal:proof,base,local,triple});
assert.equal(scratch.status,'SCRATCH_GIT_PATCH_PASS');
const bytes=Buffer.from('original file\n');
const entry={path:'README.md',size:bytes.length,sha:gitBlob(bytes),mode:'100644'};
const tree={repository:repo.full_name,baseSha:sha,treeSha:'b'.repeat(40),blobs:[{entry,bytes}]};
const input={proof,base,local,triple,scratch,tree};
const good=evaluate(input);
assert.equal(good.status,'DIFFERENTIAL_TREE_AGREEMENT_NO_EXECUTION');
assert.equal(audit(good).status,'PASS');
assert.equal(good.mayCreatePR,false);assert.equal(good.independentAlgorithm,true);
const badBefore=evaluate(input,{independentFn:root=>{
 const files=independentInventory(root);
 return files.length===1?files.map(f=>({...f,sha256:'0'.repeat(64)})):files;
}});
assert.equal(badBefore.status,'HOLD');
assert.equal(badBefore.reasons[0],'BEFORE_INVENTORY_DISAGREEMENT');
const badAfter=evaluate(input,{independentFn:root=>{
 const files=independentInventory(root);
 return files.length===2?files.map(f=>({...f,executable:!f.executable})):files;
}});
assert.equal(badAfter.status,'HOLD');
assert.equal(badAfter.reasons[0],'AFTER_INVENTORY_DISAGREEMENT');
const tampered={...good,mayMerge:true};
assert.equal(audit(tampered).status,'HOLD');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'jane-b176-independent-'));
try{
 fs.mkdirSync(path.join(dir,'nested'));fs.writeFileSync(path.join(dir,'nested','a.txt'),'a');
 assert.equal(independentInventory(dir)[0].path,'nested/a.txt');
 fs.symlinkSync('nested/a.txt',path.join(dir,'link'));
 assert.throws(()=>independentInventory(dir),/INDEPENDENT_SYMLINK/);
}finally{fs.rmSync(dir,{recursive:true,force:true})}
assert.equal(registry([good,badAfter]).counts.held,1);
console.log('PASS B176: independent walk vs B174 at before/after; mismatches HOLD; no code or write authority');
