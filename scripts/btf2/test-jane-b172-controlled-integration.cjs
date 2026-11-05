'use strict';
const assert=require('node:assert/strict');
const {build}=require('./jane-b168-proof-proposal.cjs');
const {bind}=require('./jane-b171-triple-evidence.cjs');
const {integrate,verifyInputs,report}=require('./jane-b172-controlled-integration.cjs');
const repo={full_name:'DavidWise01/jane',default_branch:'main',private:false,visibility:'public',archived:false,disabled:false,fork:false};
const policy={schema:'FORMIC-REPO-POLICY-v1',enabled:true,allowed_repairs:['BUG_REPORT_TEMPLATE'],max_open_pull_requests:1};
const evidence={repository:repo.full_name,status:'POLICY_EVIDENCE_PRESENT',mayCreatePR:false,mayMerge:false,mayRetry:false};
const proposal=build({repo,policy,b167:evidence,baseSha:'a'.repeat(40),observedAt:'2026-11-05T00:00:00Z'});
const base={schema:'JANE-B169-DRIFT-AND-CI-v1',repository:repo.full_name,
 proposalSha256:proposal.sha256,baseSha:'a'.repeat(40),observedSha:'a'.repeat(40),
 status:'BASE_OBSERVED_PASS_NOT_PROPOSAL_VALIDATED',proposalChecksExecuted:false,proposalChecksPassed:false,
 mayCreatePR:false,mayMerge:false,mayRetry:false};
const local={schema:'JANE-B170-ISOLATED-REPAIR-EVALUATION-v1',status:'LOCAL_CHECKS_PASS',
 repository:repo.full_name,proposalSha256:proposal.sha256,baseSha:'a'.repeat(40),
 localChecksPassed:true,workspaceDeleted:true,proposalTestsExecuted:true,githubCiObserved:false,
 githubCiPassed:false,repositoryCodeExecuted:false,mayCreatePR:false,mayMerge:false,mayRetry:false,
 checks:['PATCH_BYTES','PATCH_SHA256','FIXED_TEMPLATE','ISSUE_TEMPLATE_FRONT_MATTER','REPRO_STEPS','EXPECTED_AND_ACTUAL','SECRET_HYGIENE'].map(name=>({name,status:'PASS'}))};
const clock='2026-11-05T20:00:00Z';
const triple=bind({proof:proposal,base,local,baseObservedAt:clock,localEvaluatedAt:clock,nowIso:clock});
assert.equal(triple.status,'EVIDENCE_BOUND_NO_EXECUTION');
assert.deepEqual(verifyInputs({proposal,base,local,triple}),[]);
const good=integrate({proposal,base,local,triple});
assert.equal(good.status,'SCRATCH_GIT_PATCH_PASS');
assert.equal(good.scratchRemoved,true);
assert.equal(good.patchApplied,true);
assert.equal(good.targetRepoCiExecuted,false);
assert.equal(good.mayCreatePR,false);
assert.equal(good.checks.length,6);
const changed={...base,baseSha:'b'.repeat(40)};
assert.equal(integrate({proposal,base:changed,local,triple}).status,'HOLD');
const tamper=JSON.parse(JSON.stringify(triple));tamper.safety.mayMerge=true;
assert.equal(integrate({proposal,base,local,triple:tamper}).status,'HOLD');
const denied=integrate({proposal,base,local,triple},{gitFn:()=>({ok:false})});
assert.equal(denied.status,'HOLD');assert.equal(denied.scratchRemoved,true);
const results=report([good,denied]);assert.equal(results.counts.passed,1);
console.log('PASS B172 git apply --check and apply on disposable scratch, exact patch, mismatch HOLD, no repo CI/writes');
