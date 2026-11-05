'use strict';
const assert=require('node:assert/strict');
const {evaluate,decodeFile}=require('./jane-b167-authorization.cjs');
const {hash}=require('./jane-b165-owner-intent.cjs');
const {blobSha}=require('./jane-b166-live-provenance.cjs');
const repo='DavidWise01/jane',now='2026-11-05T18:00:00Z';
const intent={schema:'FORMIC-RETRY-INTENT-v1',repository:repo,repair:'BUG_REPORT_TEMPLATE',revision:2,allow_retry:true,previous_pr:7,previous_head_sha:'a'.repeat(40),rationale:'Reviewed the prior closed proposal carefully.',expires_at:'2026-11-06T18:00:00Z'};
const approval={schema:'FORMIC-RETRY-AUTHORIZATION-v1',enabled:true,repository:repo,repair:'BUG_REPORT_TEMPLATE',
  revision:1,intent_revision:2,previous_pr:7,previous_head_sha:intent.previous_head_sha,intent_digest:hash(intent),
  allowed_actions:['REVIEW_FOR_DRAFT_PR'],expires_at:'2026-11-06T18:00:00Z',default_branch:'main'};
const provenance={status:'OWNER_INTENT_EVIDENCE_PRESENT',grantWriteAuthority:false};
const history={disposition:'COOLDOWN_ELAPSED_OWNER_RESET_REQUIRED'};
const branchProtection={enforce_admins:{enabled:true},required_pull_request_reviews:{required_approving_review_count:1}};
const base={repo,intent,approval,provenance,history,branchProtection,defaultBranch:'main',at:now};
const run=overrides=>evaluate({...base,...overrides});
assert.equal(run({}).status,'POLICY_EVIDENCE_PRESENT');
assert.equal(run({}).mayCreatePR,false);
assert.equal(run({}).humanAuthorizationVerified,false);
assert.equal(run({approval:{...approval,enabled:false}}).status,'HOLD');
assert.equal(run({approval:{...approval,intent_digest:'wrong'}}).status,'HOLD');
assert.equal(run({approval:{...approval,previous_pr:8}}).status,'HOLD');
assert.equal(run({approval:{...approval,allowed_actions:['REVIEW_FOR_DRAFT_PR','AUTO_MERGE']}}).status,'HOLD');
assert.equal(run({approval:{...approval,expires_at:'2026-11-04T00:00:00Z'}}).status,'HOLD');
assert.equal(run({branchProtection:null}).status,'HOLD');
assert.equal(run({history:{disposition:'HOLD_COOLDOWN'}}).status,'HOLD');
assert.equal(run({provenance:{status:'HOLD',grantWriteAuthority:false}}).status,'HOLD');
const raw=JSON.stringify(approval),content={type:'file',path:'.formic/retry-authorization.json',encoding:'base64',
  content:Buffer.from(raw).toString('base64'),size:Buffer.byteLength(raw),sha:blobSha(raw)};
assert.equal(decodeFile(content,'.formic/retry-authorization.json').status,'FILE_VERIFIED');
assert.equal(decodeFile({...content,sha:'0'.repeat(40)},'.formic/retry-authorization.json').status,'HOLD');
console.log('PASS B167 independent policy unit gates');

const {inspect}=require('./jane-b167-authorization.cjs');
const pin='b'.repeat(40),intentCommit='c'.repeat(40),approvalCommit='d'.repeat(40);
const original=Buffer.from(JSON.stringify(intent),'utf8');
const authorized=Buffer.from(JSON.stringify(approval),'utf8');
const file=(buf,path)=>({type:'file',path,encoding:'base64',content:buf.toString('base64'),
  size:buf.length,sha:blobSha(buf.toString('utf8'))});
const intentFile=file(original,'.formic/retry-intent.json');
const approvalFile=file(authorized,'.formic/retry-authorization.json');
const commit=(sha,source)=>({sha,files:[{filename:source.path,status:'modified',sha:source.sha}],
  commit:{verification:{verified:true}},author:{login:'DavidWise01'},committer:{login:'DavidWise01'}});
const previous=[{number:7,state:'closed',created_at:'2026-09-01T00:00:00Z',
  closed_at:'2026-09-20T00:00:00Z',merged_at:null,
  head:{ref:'formic/b161-bug-report',sha:intent.previous_head_sha}}];
const mockRepo={full_name:repo,private:false,visibility:'public',archived:false,disabled:false,
  fork:false,default_branch:'main'};
function transport(overrides={}){
 return async route=>{
  if(route.includes('/git/ref/heads/'))return {object:{sha:pin}};
  if(route.includes('/contents/.formic/retry-intent.json'))return intentFile;
  if(route.includes('/contents/.formic/retry-authorization.json'))return approvalFile;
  if(route.includes('/commits?path=.formic%2Fretry-intent.json'))return [{sha:intentCommit}];
  if(route.includes('/commits?path=.formic%2Fretry-authorization.json'))return [{sha:approvalCommit}];
  if(route.includes('/commits/'+intentCommit))return commit(intentCommit,intentFile);
  if(route.includes('/commits/'+approvalCommit))return overrides.approvalCommit||commit(approvalCommit,approvalFile);
  if(route.includes('/pulls?'))return previous;
  if(route.includes('/branches/main/protection'))return overrides.protection===undefined?branchProtection:overrides.protection;
  throw Error('UNEXPECTED_MOCK_ROUTE '+route);
 };
}
(async()=>{
 const good=await inspect(mockRepo,now,'',transport());
 assert.equal(good.status,'POLICY_EVIDENCE_PRESENT');
 assert.equal(good.mayCreatePR,false);
 const badSignature=await inspect(mockRepo,now,'',transport({approvalCommit:{
   ...commit(approvalCommit,approvalFile),commit:{verification:{verified:false}}}}));
 assert.equal(badSignature.status,'HOLD');
 const noProtection=await inspect(mockRepo,now,'',transport({protection:null}));
 assert.equal(noProtection.status,'HOLD');
 console.log('PASS B167 integration mock: same pinned SHA, independent file commits, branch protection');
})().catch(e=>{console.error(e);process.exitCode=1});

