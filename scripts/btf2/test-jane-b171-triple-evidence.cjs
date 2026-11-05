'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {build}=require('./jane-b168-proof-proposal.cjs');
const {bind,audit,run}=require('./jane-b171-triple-evidence.cjs');
const repo={full_name:'DavidWise01/jane',default_branch:'main',private:false,visibility:'public',archived:false,disabled:false,fork:false};
const policy={schema:'FORMIC-REPO-POLICY-v1',enabled:true,allowed_repairs:['BUG_REPORT_TEMPLATE'],max_open_pull_requests:1};
const b167={repository:repo.full_name,status:'POLICY_EVIDENCE_PRESENT',mayCreatePR:false,mayRetry:false,mayMerge:false};
const proof=build({repo,policy,b167,baseSha:'a'.repeat(40)});
const now='2026-11-05T20:00:00Z';
const base={schema:'JANE-B169-DRIFT-AND-CI-v1',status:'BASE_OBSERVED_PASS_NOT_PROPOSAL_VALIDATED',
  repository:repo.full_name,proposalSha256:proof.sha256,baseSha:'a'.repeat(40),observedSha:'a'.repeat(40),
  proposalChecksExecuted:false,proposalChecksPassed:false,mayCreatePR:false,mayRetry:false,mayMerge:false};
const local={schema:'JANE-B170-ISOLATED-REPAIR-EVALUATION-v1',status:'LOCAL_CHECKS_PASS',
  repository:repo.full_name,proposalSha256:proof.sha256,baseSha:'a'.repeat(40),
  localChecksPassed:true,workspaceDeleted:true,proposalTestsExecuted:true,githubCiObserved:false,
  githubCiPassed:false,repositoryCodeExecuted:false,mayCreatePR:false,mayRetry:false,mayMerge:false,
  checks:['PATCH_BYTES','PATCH_SHA256','FIXED_TEMPLATE','ISSUE_TEMPLATE_FRONT_MATTER','REPRO_STEPS','EXPECTED_AND_ACTUAL','SECRET_HYGIENE'].map(name=>({name,status:'PASS'}))};
const b=()=>bind({proof,base,local,baseObservedAt:now,localEvaluatedAt:now,nowIso:now});
const good=b();assert.equal(good.status,'EVIDENCE_BOUND_NO_EXECUTION');
assert.equal(audit(good).status,'PASS');assert.equal(good.safety.mayCreatePR,false);
assert.equal(bind({proof,base:{...base,proposalSha256:'f'.repeat(64)},local,baseObservedAt:now,localEvaluatedAt:now,nowIso:now}).status,'HOLD');
assert.equal(bind({proof,base:{...base,observedSha:'b'.repeat(40)},local,baseObservedAt:now,localEvaluatedAt:now,nowIso:now}).status,'HOLD');
assert.equal(bind({proof,base,local:{...local,githubCiObserved:true},baseObservedAt:now,localEvaluatedAt:now,nowIso:now}).status,'HOLD');
assert.equal(bind({proof,base,local,baseObservedAt:'2026-11-05T19:50:00Z',localEvaluatedAt:now,nowIso:now}).status,'HOLD');
const tamper=JSON.parse(JSON.stringify(good));tamper.safety.mayMerge=true;
assert.equal(audit(tamper).status,'HOLD');
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'b171-'));
(async()=>{
 try{
  const empty=await run({dir:tmp});assert.equal(empty.status,'HOLD_NO_PROPOSALS');
  fs.writeFileSync(path.join(tmp,'proof.json'),JSON.stringify(proof));
  const result=await run({dir:tmp,now:()=>now,inspect:async()=>base,examine:()=>local});
  assert.equal(result.counts.bound,1);assert.equal(result.governance.automaticWrites,false);
  console.log('PASS B171: 3-way digest, base revision, TTL, witness distinctness, tamper HOLD, zero writes');
 }finally{fs.rmSync(tmp,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
