'use strict';
const assert=require('node:assert/strict');
const v=require('./jane-b166-live-provenance.cjs');
const {audit}=require('./jane-b165-owner-intent.cjs');
const owner='DavidWise01',now='2026-11-05T15:00:00Z';
const repo={full_name:'DavidWise01/jane',default_branch:'main',private:false,visibility:'public',archived:false,disabled:false,fork:false};
const previousSha='a'.repeat(40),pathCommit='b'.repeat(40),defaultCommit='c'.repeat(40);
const intent={schema:'FORMIC-RETRY-INTENT-v1',repository:repo.full_name,repair:'BUG_REPORT_TEMPLATE',revision:2,allow_retry:true,previous_pr:7,previous_head_sha:previousSha,rationale:'Reviewed original failure and documented a new revision.',expires_at:'2026-11-07T15:00:00Z'};
const raw=JSON.stringify(intent),blob=v.blobSha(raw);
const file={type:'file',path:v.INTENT_PATH,encoding:'base64',size:Buffer.byteLength(raw),content:Buffer.from(raw).toString('base64'),sha:blob};
const commits=[{sha:pathCommit},{sha:'d'.repeat(40)}],detail={sha:pathCommit,files:[{filename:v.INTENT_PATH,status:'modified',sha:blob}],commit:{verification:{verified:true}},author:{login:owner},committer:{login:owner}};
const previous=[{number:7,state:'closed',created_at:'2026-09-01T00:00:00Z',closed_at:'2026-09-20T00:00:00Z',merged_at:null,head:{ref:'formic/b161-bug-report',sha:previousSha},html_url:'https://github.com/DavidWise01/jane/pull/7'}];
assert.equal(v.blobSha('abc'),'f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f');
assert.equal(v.resolveAttestation(repo,file,commits,detail,now).status,'EVIDENCE_PRESENT');
assert.equal(v.resolveAttestation(repo,{...file,sha:'0'.repeat(40)},commits,detail,now).status,'HOLD');
assert.equal(v.resolveAttestation(repo,{...file,size:file.size+1},commits,detail,now).status,'HOLD');
assert.equal(v.resolveAttestation(repo,file,commits,{...detail,files:[{filename:v.INTENT_PATH,status:'modified',sha:'0'.repeat(40)}]},now).status,'HOLD');
assert.equal(v.resolveAttestation(repo,file,commits,{...detail,author:{login:'Other'}},now).status,'HOLD');
assert.equal(v.resolveAttestation(repo,file,commits,{...detail,commit:{verification:{verified:false}}},now).status,'HOLD');
const fetcher=async route=>{
 if(route.includes('/git/ref/heads/'))return{object:{sha:defaultCommit}};
 if(route.includes('/contents/')){assert.ok(route.includes('ref='+defaultCommit));return file}
 if(route.includes('/commits?')){assert.ok(route.includes('sha='+defaultCommit));return commits}
 if(route.includes('/commits/'))return detail;
 if(route.includes('/pulls?'))return previous;
 throw Error('UNEXPECTED_ROUTE '+route);
};
(async()=>{
 const record=await v.examine(repo,now,'',fetcher);
 assert.equal(record.status,'OWNER_INTENT_EVIDENCE_PRESENT');
 assert.equal(record.grantWriteAuthority,false);
 assert.equal((await v.examine(repo,now,'',async route=>route.includes('/git/ref/heads/')?{object:{sha:'NOT_A_SHA'}}:fetcher(route))).status,'HOLD');
 assert.equal((await v.examine(repo,now,'',async route=>route.includes('/contents/')?null:fetcher(route))).status,'HOLD');
 assert.equal((await v.examine({...repo,private:true},now,'',fetcher)).status,'HOLD');
 const policy={schema:'FORMIC-REPO-POLICY-v1',enabled:true,allowed_repairs:['BUG_REPORT_TEMPLATE'],max_open_pull_requests:1};
 const report=await v.observe({repos:[repo],nowIso:now,policyFn:async()=>policy,examineFn:async()=>record});
 assert.equal(audit(report).status,'PASS');
 assert.equal(report.events[0].evidence.grantWriteAuthority,false);
 console.log('PASS B166: exact default ref, path commit, blob bytes, signed evidence, previous PR, no write rights');
})().catch(e=>{console.error(e);process.exitCode=1});
