'use strict';
const assert=require('node:assert/strict');
const m=require('./jane-b165-owner-intent.cjs');
const repo='DavidWise01/jane',sha='a'.repeat(40),now='2026-11-05T15:00:00Z';
const history={repo,disposition:'COOLDOWN_ELAPSED_OWNER_RESET_REQUIRED',events:[
{pr:7,kind:'CLOSED_UNMERGED',headSha:sha}]};
const intent={schema:'FORMIC-RETRY-INTENT-v1',repository:repo,repair:'BUG_REPORT_TEMPLATE',revision:2,allow_retry:true,
 previous_pr:7,previous_head_sha:sha,rationale:'Explicitly review the previous failure before any later repair.',expires_at:'2026-11-07T15:00:00Z'};
const att={repository:repo,path:'.formic/retry-intent.json',ref:'main',default_branch:'main',
 commit:{verification:{verified:true},author:{login:'DavidWise01'},committer:{login:'DavidWise01'}},reviewedPolicyDigest:m.hash(intent)};
const evaluate=(i=intent,a=att,h=history)=>m.validateIntent(repo,h,i,a,now);
assert.equal(evaluate().status,'OWNER_INTENT_EVIDENCE_PRESENT');
assert.equal(evaluate().grantWriteAuthority,false);
assert.equal(evaluate({...intent,revision:1}).status,'HOLD');
assert.equal(evaluate({...intent,allow_retry:false}).status,'HOLD');
assert.equal(evaluate({...intent,previous_pr:8}).status,'HOLD');
assert.equal(evaluate({...intent,expires_at:'2026-11-04T15:00:00Z'}).status,'HOLD');
assert.equal(evaluate(intent,{...att,commit:{...att.commit,verification:{verified:false}}}).status,'HOLD');
assert.equal(evaluate(intent,{...att,commit:{...att.commit,author:{login:'Other'}}}).status,'HOLD');
assert.equal(evaluate(intent,{...att,ref:'feature'}).status,'HOLD');
assert.equal(evaluate(intent,{...att,reviewedPolicyDigest:'bad'}).status,'HOLD');
assert.equal(evaluate(intent,att,{...history,disposition:'HOLD_COOLDOWN'}).status,'HOLD');
const report=m.ledger([evaluate(),{...evaluate(),repository:'DavidWise01/another'}]);
assert.equal(m.audit(report).status,'PASS');
const corrupt=JSON.parse(JSON.stringify(report));corrupt.events[0].evidence.grantWriteAuthority=true;
assert.equal(m.audit(corrupt).status,'HOLD');
assert.equal(m.validateIntent('other/repo',history,intent,att,now).status,'HOLD');
console.log('PASS B165: owner-intent evidence, revision, expiry, PR pin, SHA pin, default ref, verified commit, integrity, no retry authority');
