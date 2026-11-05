'use strict';
/**
 * B165: explicit owner-intent evidence. READ ONLY. This kernel never creates a PR.
 * GitHub's commit verification is evidence, not an independent legal identity proof.
 */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {versionedHistory}=require('./jane-b164-durable-repair.cjs');
const OWNER='DavidWise01',REPAIR='BUG_REPORT_TEMPLATE';
const hash=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
function scope(repo){return typeof repo==='string'&&/^DavidWise01\/[A-Za-z0-9_.-]+$/.test(repo)}
function validateIntent(repo,history,intent,attestation,nowIso){
 const reasons=[];
 if(!scope(repo))reasons.push('OUT_OF_SCOPE');
 if(!history||history.repo!==repo||!Array.isArray(history.events))reasons.push('HISTORY_MISMATCH');
 if(!intent||intent.schema!=='FORMIC-RETRY-INTENT-v1')reasons.push('INTENT_SCHEMA');
 if(!intent||intent.repository!==repo||intent.repair!==REPAIR)reasons.push('INTENT_SCOPE');
 if(!Number.isInteger(intent?.revision)||intent.revision<2)reasons.push('REVISION_REQUIRED');
 if(intent?.allow_retry!==true)reasons.push('EXPLICIT_RETRY_FLAG_REQUIRED');
 if(typeof intent?.previous_pr!=='number'||!Number.isInteger(intent.previous_pr)||intent.previous_pr<1)reasons.push('PR_REFERENCE_REQUIRED');
 if(typeof intent?.previous_head_sha!=='string'||!/^[a-f0-9]{40}$/i.test(intent.previous_head_sha))reasons.push('HEAD_SHA_REQUIRED');
 if(typeof intent?.rationale!=='string'||intent.rationale.trim().length<12)reasons.push('RATIONALE_REQUIRED');
 if(typeof intent?.expires_at!=='string'||!Number.isFinite(Date.parse(intent.expires_at)))reasons.push('EXPIRATION_REQUIRED');
 if(!Number.isFinite(Date.parse(nowIso)))reasons.push('INVALID_CLOCK');
 else if(Number.isFinite(Date.parse(intent?.expires_at))&&Date.parse(intent.expires_at)<=Date.parse(nowIso))reasons.push('INTENT_EXPIRED');
 if(history?.disposition!=='COOLDOWN_ELAPSED_OWNER_RESET_REQUIRED')reasons.push('HISTORY_NOT_RECOVERABLE');
 const previous=history?.events?.find(e=>e.pr===intent?.previous_pr);
 if(!previous||previous.kind!=='CLOSED_UNMERGED'||previous.headSha!==intent?.previous_head_sha)reasons.push('PREVIOUS_PR_MISMATCH');
 const latest=history?.events?.at(-1);
 if(previous&&latest&&latest.pr!==previous.pr)reasons.push('NOT_LATEST_PR');
 if(!attestation||attestation.repository!==repo||attestation.path!=='.formic/retry-intent.json'||
    attestation.ref!==attestation.default_branch||typeof attestation.default_branch!=='string')reasons.push('DEFAULT_BRANCH_EVIDENCE_REQUIRED');
 if(attestation?.commit?.verification?.verified!==true)reasons.push('VERIFIED_COMMIT_REQUIRED');
 if(attestation?.commit?.author?.login!==OWNER||attestation?.commit?.committer?.login!==OWNER)reasons.push('OWNER_COMMIT_ATTRIBUTION_REQUIRED');
 if(attestation?.reviewedPolicyDigest!==hash(intent))reasons.push('INTENT_DIGEST_MISMATCH');
 const unique=[...new Set(reasons)];
 return {status:unique.length?'HOLD':'OWNER_INTENT_EVIDENCE_PRESENT',reasons:unique,repository:repo,repair:REPAIR,
  previousPr:intent?.previous_pr??null,revision:intent?.revision??null,
  grantWriteAuthority:false,allowAutoMerge:false,allowDefaultBranchWrite:false,
  authenticationLimit:'GITHUB_VERIFIED_COMMIT_AND_ACCOUNT_ATTRIBUTION_ARE_EVIDENCE_NOT_INDEPENDENT_IDENTITY_PROOF'};
}
function ledger(entries){
 if(!Array.isArray(entries))throw Error('INVALID_ENTRIES');
 const events=[];let previous='GENESIS';
 for(const e of [...entries].sort((a,b)=>String(a.repository).localeCompare(String(b.repository)))){
  if(!scope(e.repository)||!['HOLD','OWNER_INTENT_EVIDENCE_PRESENT'].includes(e.status))throw Error('INVALID_RECORD');
  const body={seq:events.length+1,previous,evidence:JSON.parse(JSON.stringify(e))};
  events.push({...body,hash:hash(body)});previous=events.at(-1).hash;
 }
 return{schema:'JANE-B165-OWNER-INTENT-EVIDENCE-v1',mode:'OBSERVATION_ONLY',events,head:previous,
  governance:{isaDefined:false,noQuorum:true,autoRetry:false,autoMerge:false,noDefaultBranchWrites:true}};
}
function audit(record){
 if(record?.schema!=='JANE-B165-OWNER-INTENT-EVIDENCE-v1'||!Array.isArray(record.events))return{status:'HOLD'};
 let previous='GENESIS';
 for(let i=0;i<record.events.length;i++){
  const e=record.events[i],{hash:provided,...body}=e;
  if(body.seq!==i+1||body.previous!==previous||provided!==hash(body)||!scope(body.evidence?.repository))return{status:'HOLD'};
  previous=provided;
 }
 return{status:record.head===previous&&record.governance?.autoRetry===false?'PASS':'HOLD',entries:record.events.length};
}
function runFixture(file,out){
 const input=JSON.parse(fs.readFileSync(file,'utf8')),rows=[];
 for(const record of input.records||[]){
  const h=versionedHistory(record.repository,record.prs,record.nowIso);
  rows.push(validateIntent(record.repository,h,record.intent,record.attestation,record.nowIso));
 }
 const report=ledger(rows);if(audit(report).status!=='PASS')throw Error('LEDGER_HOLD');
 fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');
 return report;
}
if(require.main===module){
 try{
  const args=process.argv.slice(2);
  // B165 intentionally does not accept an --apply/write mode, and refuses live
  // ingestion until full GitHub evidence retrieval is explicitly designed.
  if(!args.includes('--fixture'))throw Error('HOLD_LIVE_OWNER_ATTESTATION_NOT_WIRED');
  const file=args[args.indexOf('--fixture')+1],out=args.includes('--output')?args[args.indexOf('--output')+1]:'ecosystem/reports/b165-fixture.json';
  const r=runFixture(file,out);console.log(JSON.stringify({status:'PASS',events:r.events.length,mode:'OBSERVATION_ONLY'}));
 }catch(e){console.error(e.message);process.exitCode=1}
}
module.exports={OWNER,REPAIR,scope,validateIntent,ledger,audit,runFixture,hash};
