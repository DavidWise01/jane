'use strict';
/**
 * B163: Pure read-only repair memory derived from B162's GitHub PR-history and
 * check observations. No repository writes, no ISA, and no automatic approval.
 */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const OWNER='DavidWise01';
const REPAIR='BUG_REPORT_TEMPLATE';
const ACCEPT=new Set([
 'NO_FORMIC_PR','REVIEW_READY_NO_AUTO_MERGE','HOLD_CHECKS_FAILED',
 'HOLD_CHECKS_PENDING','HOLD_CHECKS_UNAVAILABLE','HOLD_NO_CHECK_EVIDENCE',
 'HOLD_CLOSED_PR_RETRY_SUPPRESSED','MERGED_EXTERNALLY_OBSERVED',
 'HOLD_NON_DRAFT_PR','HOLD_INSPECTION_FAILED','HOLD_PR_HISTORY_TRUNCATED',
 'HOLD_CHECKS_TRUNCATED','HOLD_INVALID_PR_DATA','HOLD_POLICY_FETCH_FAILED'
]);
const hash=o=>crypto.createHash('sha256').update(JSON.stringify(o)).digest('hex');
const scoped=s=>typeof s==='string'&&/^DavidWise01\/[A-Za-z0-9_.-]+$/.test(s);
function classify(row){
 if(!row||!scoped(row.repo))return {state:'HOLD_INVALID_REPO',action:'NO_ACTION',reason:'OUT_OF_SCOPE'};
 const d=row.decision,checks=row.checks||{};
 if(!ACCEPT.has(d))return {state:'HOLD_UNKNOWN_DECISION',action:'NO_ACTION',reason:'UNRECOGNIZED_DISPOSITION'};
 if(d==='NO_FORMIC_PR')return{state:'UNTRIED',action:'ELIGIBILITY_ONLY',reason:'NO_FORMIC_HISTORY'};
 if(d==='REVIEW_READY_NO_AUTO_MERGE')
   return{state:'CHECKS_GREEN',action:'HUMAN_REVIEW_ONLY',reason:'CHECKS_ARE_NOT_MERGE_AUTHORITY'};
 if(d==='MERGED_EXTERNALLY_OBSERVED')
   return{state:'MERGED_EXTERNALLY',action:'OBSERVE_ONLY',reason:'NOT_ATTRIBUTED_TO_FORMIC'};
 if(d==='HOLD_CLOSED_PR_RETRY_SUPPRESSED')
   return{state:'CLOSED_UNMERGED',action:'SUPPRESS_REPAIR',reason:'REPOSITORY_CLOSED_PREVIOUS_PROPOSAL'};
 if(d==='HOLD_CHECKS_FAILED')
   return{state:'FAILED_CHECKS',action:'SUPPRESS_REPAIR',reason:'PR_HEAD_CHECK_FAILURE'};
 if(d==='HOLD_CHECKS_PENDING')
   return{state:'PENDING_CHECKS',action:'HOLD',reason:'AWAIT_EXISTING_PR_CHECKS'};
 if(d==='HOLD_NON_DRAFT_PR')
   return{state:'NON_DRAFT',action:'HOLD',reason:'REPOSITORY_REVIEW_REQUIRED'};
 return{state:'INSUFFICIENT_EVIDENCE',action:'HOLD',reason:d};
}
function build(report){
 if(!report||report.schema!=='JANE-B162-FORMIC-PR-VERIFICATION-v1'||report.owner!==OWNER||
  report.mode!=='READ_ONLY'||!Array.isArray(report.results))throw Error('INVALID_B162_REPORT');
 const rows=[];
 const used=new Set();
 for(const r of report.results){
  if(!scoped(r.repo))throw Error('OUT_OF_SCOPE_ROW');
  if(used.has(r.repo))throw Error('DUPLICATE_REPO_IN_REPORT');
  used.add(r.repo);
  const c=classify(r);
  // Preserve the exact observed disposition, head identity, and check failures.
  rows.push({
   repo:r.repo,repair:REPAIR,attemptKey:r.repo+'#'+REPAIR,
   observedDecision:r.decision,headSha:r.pr?.headSha||null,
   prNumber:Number.isInteger(r.pr?.number)?r.pr.number:null,
   evidence:{checkState:r.checks?.state||null,failed:Array.isArray(r.checks?.failed)?r.checks.failed:[],pending:Array.isArray(r.checks?.pending)?r.checks.pending:[]},
   ...c,physicalPromotion:false
  });
 }
 rows.sort((a,b)=>a.repo.localeCompare(b.repo));
 const events=[];let previous='GENESIS';
 for(let i=0;i<rows.length;i++){
  const payload={sequence:i+1,previous,evidence:rows[i]};
  const entry={...payload,hash:hash(payload)};events.push(entry);previous=entry.hash;
 }
 const counts={observed:rows.length,untried:0,green:0,failed:0,closedSuppressed:0,hold:0};
 for(const r of rows){
  if(r.state==='UNTRIED')counts.untried++;
  else if(r.state==='CHECKS_GREEN')counts.green++;
  else if(r.state==='FAILED_CHECKS')counts.failed++;
  else if(r.state==='CLOSED_UNMERGED')counts.closedSuppressed++;
  else if(r.action==='HOLD')counts.hold++;
 }
 return{schema:'JANE-B163-FORMIC-REPAIR-MEMORY-v1',
  owner:OWNER,sourceSchema:report.schema,sourceObservedAt:report.observedAt||null,
  mode:'DERIVED_READ_ONLY',repair:REPAIR,counts,events,head:previous,
  governance:{quorum:false,isaDefined:false,sourceWitnesses:['a1','b1','c1'],
   noAutomaticWrites:true,noAutomaticMerges:true,retryPolicy:'PER_PR_HISTORY',
   physicalPromotion:false},
  limitations:['REPORT_SNAPSHOT_NOT_GLOBAL_REPO_MEMORY','CLOSED_PR_HISTORY_FROM_GITHUB_IS_DURABLE_SUPPRESSION_SOURCE','HASH_CHAIN_DETECTS_ACCIDENTAL_TAMPERING_NOT_VERIFIED_AUTHORSHIP']};
}
function audit(report){
 if(!report||!Array.isArray(report.events))return{status:'HOLD',reason:'INVALID_LEDGER'};
 let prev='GENESIS';
 for(let i=0;i<report.events.length;i++){
  const event=report.events[i],{hash:given,...payload}=event;
  if(payload.sequence!==i+1||payload.previous!==prev||given!==hash(payload)||
    !scoped(payload.evidence?.repo)||payload.evidence?.physicalPromotion!==false)
    return{status:'HOLD',reason:'LEDGER_CHAIN'};
  prev=given;
 }
 if(report.head!==prev||report.counts?.observed!==report.events.length||report.governance?.noAutomaticMerges!==true)
  return{status:'HOLD',reason:'LEDGER_SUMMARY'};
 return{status:'PASS',entries:report.events.length,head:prev,noQuorum:true};
}
function suppression(memory,repo,repair=REPAIR){
 if(!scoped(repo)||repair!==REPAIR)return{decision:'HOLD_INVALID_SCOPE'};
 const row=memory?.events?.find(e=>e.evidence?.repo===repo&&e.evidence.repair===repair)?.evidence;
 if(!row)return{decision:'NO_OBSERVATION_NOT_AUTHORIZED'};
 return row.action==='SUPPRESS_REPAIR'?{decision:'SUPPRESS_REPAIR',reason:row.reason}:
   {decision:'NO_AUTOMATIC_AUTHORIZATION',lastState:row.state};
}
function main(){
 const args=process.argv.slice(2),src=args.includes('--input')?args[args.indexOf('--input')+1]:'ecosystem/reports/b162-latest.json',
  out=args.includes('--output')?args[args.indexOf('--output')+1]:'ecosystem/reports/b163-latest.json';
 const data=build(JSON.parse(fs.readFileSync(src,'utf8')));
 if(audit(data).status!=='PASS')throw Error('MEMORY_LEDGER_FAILED_AUDIT');
 fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(data,null,2)+'\n');
 console.log(JSON.stringify({status:'PASS',mode:data.mode,counts:data.counts,head:data.head}));
}
if(require.main===module)try{main()}catch(e){console.error('HOLD '+e.message);process.exitCode=1}
module.exports={REPAIR,classify,build,audit,suppression};
