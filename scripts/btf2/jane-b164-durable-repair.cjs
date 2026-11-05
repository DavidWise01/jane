'use strict';
/**
 * B164: durable PR-history-derived repair lifecycle. Pure evaluation.
 * A cooldown is a waiting boundary, never consent to create another PR.
 */
const fs=require('node:fs'), path=require('node:path'),crypto=require('node:crypto');
const {publicRepos,repoGate,policyGate,readPolicy,BRANCH}=require('./jane-b161-formic-agent.cjs');
const {gitApi}=require('./jane-b162-formic-verifier.cjs');
const OWNER='DavidWise01',REPAIR='BUG_REPORT_TEMPLATE',COOLDOWN_DAYS=30;
const sha=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const scoped=s=>typeof s==='string'&&/^DavidWise01\/[A-Za-z0-9_.-]+$/.test(s);
function validTime(s){const n=Date.parse(s);return Number.isFinite(n)?n:null}
function versionedHistory(repo,prs,nowIso,options={}){
 if(!scoped(repo)||!Array.isArray(prs)||!Number.isFinite(Date.parse(nowIso)))throw Error('INVALID_HISTORY');
 const now=Date.parse(nowIso),days=options.cooldownDays??COOLDOWN_DAYS;
 if(!Number.isInteger(days)||days<1||days>365)throw Error('INVALID_COOLDOWN');
 if(prs.length>100) return{repo,repair:REPAIR,disposition:'HOLD_HISTORY_TRUNCATED',events:[],cooldownDays:days,remainingDays:null,ownerResetRequired:true};
 const seen=new Set(),events=[];
 for(const p of prs){
  if(!Number.isInteger(p.number)||p.number<1||seen.has(p.number))throw Error('INVALID_DUPLICATE_PR_NUMBER');
  seen.add(p.number);
  const created=validTime(p.created_at),closed=p.closed_at?validTime(p.closed_at):null,merged=p.merged_at?validTime(p.merged_at):null;
  if(created===null||created>now||closed!==null&&(closed<created||closed>now)||merged!==null&&(merged<created||merged>now))throw Error('INVALID_PR_TIMELINE');
  if(p.head?.ref!==BRANCH)throw Error('UNEXPECTED_BRANCH');
  const kind=merged!==null?'MERGED_EXTERNALLY':p.state==='open'?'OPEN_PR':p.state==='closed'?'CLOSED_UNMERGED':'UNKNOWN_PR_STATE';
  events.push({pr:p.number,kind,createdAt:p.created_at,closedAt:p.closed_at||null,mergedAt:p.merged_at||null,headSha:p.head?.sha||null,sourceUrl:p.html_url||null});
 }
 events.sort((a,b)=>a.createdAt.localeCompare(b.createdAt)||a.pr-b.pr);
 let disposition='NO_PREVIOUS_PROPOSAL',remainingDays:null,ownerResetRequired=false;
 if(events.length){
  const latest=events.at(-1);
  if(latest.kind==='OPEN_PR'){disposition='HOLD_EXISTING_OPEN_PR';ownerResetRequired=true}
  else if(latest.kind==='MERGED_EXTERNALLY'){disposition='ALREADY_APPLIED_OBSERVE_ONLY';ownerResetRequired=true}
  else if(latest.kind==='CLOSED_UNMERGED'){
   const end=validTime(latest.closedAt);
   const elapsed=Math.floor((now-end)/(86400000));
   remainingDays=Math.max(0,days-elapsed);
   disposition=remainingDays>0?'HOLD_COOLDOWN':'COOLDOWN_ELAPSED_OWNER_RESET_REQUIRED';
   ownerResetRequired=true;
  }else{disposition='HOLD_UNKNOWN_HISTORY';ownerResetRequired=true}
 }
 // A failure/closure is never "forgotten" when cooldown ends.
 return{repo,repair:REPAIR,disposition,events,cooldownDays:days,remainingDays,ownerResetRequired,
   reusableConsent:false,noAutomaticRetry:true,physicalPromotion:false};
}
function snapshot(entries,observedAt){
 if(!Number.isFinite(Date.parse(observedAt))||!Array.isArray(entries))throw Error('INVALID_SNAPSHOT');
 const ordered=[...entries].sort((a,b)=>a.repo.localeCompare(b.repo)),seen=new Set();
 const chain=[];let prev='GENESIS';
 for(const row of ordered){
  if(!scoped(row.repo)||seen.has(row.repo))throw Error('DUPLICATE_OR_FOREIGN_REPO');
  seen.add(row.repo);
  const body={sequence:chain.length+1,previous:prev,entry:row},hash=sha(body);
  chain.push({...body,hash});prev=hash;
 }
 const counts={observed:chain.length,cooldown:0,ownerResetRequired:0,noPreviousProposal:0,open:0};
 for(const x of ordered){
  if(x.disposition==='HOLD_COOLDOWN')counts.cooldown++;
  if(x.ownerResetRequired)counts.ownerResetRequired++;
  if(x.disposition==='NO_PREVIOUS_PROPOSAL')counts.noPreviousProposal++;
  if(x.disposition==='HOLD_EXISTING_OPEN_PR')counts.open++;
 }
 return{schema:'JANE-B164-DURABLE-REPAIR-BOUND-v1',owner:OWNER,observedAt,repair:REPAIR,mode:'READ_ONLY',
  provenance:'GITHUB_PR_HISTORY',version:1,counts,events:chain,head:prev,
  governance:{quorum:false,isaDefined:false,autoRetry:false,autoMerge:false,defaultBranchWrite:false,observerDepth:1,sourceWitnesses:['a1','b1','c1']},
  limitations:['PR_HISTORY_DURABLE_GITHUB_SOURCE','ARTIFACT_30_DAY_RETENTION','COOLDOWN_ELAPSE_IS_NOT_NEW_AUTHORIZATION']};
}
function audit(record){
 if(!record||record.schema!=='JANE-B164-DURABLE-REPAIR-BOUND-v1'||record.mode!=='READ_ONLY'||!Array.isArray(record.events))return{status:'HOLD',reason:'SCHEMA'};
 let prev='GENESIS',repos=new Set();
 for(let i=0;i<record.events.length;i++){
  const item=record.events[i],{hash,...body}=item;
  if(body.sequence!==i+1||body.previous!==prev||hash!==sha(body)||!scoped(body.entry?.repo)||repos.has(body.entry.repo)||body.entry.reusableConsent!==false||body.entry.noAutomaticRetry!==true)return{status:'HOLD',reason:'CHAIN_OR_SCOPE'};
  repos.add(body.entry.repo);prev=hash;
 }
 if(record.head!==prev||record.counts?.observed!==record.events.length||record.governance?.autoMerge!==false)return{status:'HOLD',reason:'ROOT_OR_COUNTS'};
 return{status:'PASS',entries:record.events.length,head:prev,isaDefined:false};
}
async function scan({token='',observedAt=new Date().toISOString(),maxTargets=10,listing,readPolicyFn=readPolicy,fetchPrs}={}){
 if(!Number.isInteger(maxTargets)||maxTargets<1||maxTargets>10)throw Error('INVALID_TARGET_LIMIT');
 const repos=listing||await publicRepos(token);
 const eligible=[],errors=[];
 for(const repo of repos){
  if(eligible.length>=maxTargets)break;
  if(repoGate(repo)!=='ELIGIBLE')continue;
  try{const policy=await readPolicyFn(repo,token);if(policyGate(policy)==='ELIGIBLE')eligible.push(repo)}
  catch(e){errors.push({repo:repo.full_name,reason:'HOLD_POLICY_READ',detail:String(e.message).slice(0,120)})}
 }
 const results=[];
 for(const r of eligible){
  try{
   const prList=await (fetchPrs?fetchPrs(r):gitApi('/repos/'+r.full_name+'/pulls?state=all&head='+encodeURIComponent(OWNER+':'+BRANCH)+'&per_page=100&sort=created&direction=desc',token));
   // Exactly 100 means history may be incomplete; fail closed.
   if(!Array.isArray(prList)||prList.length>=100){results.push({repo:r.full_name,repair:REPAIR,disposition:'HOLD_HISTORY_TRUNCATED',events:[],cooldownDays:COOLDOWN_DAYS,remainingDays:null,ownerResetRequired:true,reusableConsent:false,noAutomaticRetry:true,physicalPromotion:false});continue}
   results.push(versionedHistory(r.full_name,prList,observedAt));
  }catch(e){results.push({repo:r.full_name,repair:REPAIR,disposition:'HOLD_PR_HISTORY_UNAVAILABLE',events:[],cooldownDays:COOLDOWN_DAYS,remainingDays:null,ownerResetRequired:true,reusableConsent:false,noAutomaticRetry:true,physicalPromotion:false})}
 }
 const output=snapshot(results,observedAt);output.discoveryHolds=errors;return output;
}
async function main(){
 const args=process.argv.slice(2),dest=args.includes('--output')?args[args.indexOf('--output')+1]:'ecosystem/reports/b164-latest.json';
 const report=await scan({token:process.env.GITHUB_TOKEN||''});
 if(audit(report).status!=='PASS')throw Error('LEDGER_FAILED');
 fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({counts:report.counts,audit:'PASS',mode:'READ_ONLY'}));
}
if(require.main===module)main().catch(e=>{console.error('HOLD '+e.message);process.exitCode=1});
module.exports={REPAIR,COOLDOWN_DAYS,versionedHistory,snapshot,audit,scan};
