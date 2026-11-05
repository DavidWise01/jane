'use strict';
/** B162: read-only GitHub PR/check observation, independent of the B161 PR writer. */
const fs=require('node:fs');
const path=require('node:path');
const {scoped,repoGate,policyGate,readPolicy,publicRepos,BRANCH}=require('./jane-b161-formic-agent.cjs');
const OWNER='DavidWise01',MAX_TARGETS=10;
function checkSummary(checks=[],statuses=[],{checksAccessible=true,statusesAccessible=true}={}){
 if(!checksAccessible||!statusesAccessible)return{state:'HOLD_CHECKS_UNAVAILABLE',checks:0,statuses:0,failed:[],pending:[]};
 if(!Array.isArray(checks)||!Array.isArray(statuses))return{state:'HOLD_INVALID_CHECK_DATA',checks:0,statuses:0,failed:[],pending:[]};
 // Evaluate latest check-run PER name+app, without confusing old rerun results with current ones.
 const latest=new Map();
 for(const c of checks){
  if(!c||typeof c.name!=='string')continue;
  const k=c.name+'|'+String(c.app?.id??'');
  const old=latest.get(k);
  if(!old||Date.parse(c.started_at||c.created_at||0)>=Date.parse(old.started_at||old.created_at||0))latest.set(k,c);
 }
 const active=[...latest.values()],failed=[],pending=[];
 for(const c of active){
  if(c.status!=='completed')pending.push(c.name);
  else if(!['success','neutral','skipped'].includes(c.conclusion))failed.push(c.name+':'+String(c.conclusion));
 }
 // Status API may have many historical contexts: only latest context counts.
 const contexts=new Map();
 for(const s of statuses){if(s&&typeof s.context==='string'&&!contexts.has(s.context))contexts.set(s.context,s)}
 for(const s of contexts.values()){
  if(['failure','error'].includes(s.state))failed.push('status:'+s.context+':'+s.state);
  else if(s.state!=='success')pending.push('status:'+s.context+':'+s.state);
 }
 if(failed.length)return{state:'HOLD_CHECKS_FAILED',checks:active.length,statuses:contexts.size,failed,pending};
 if(pending.length)return{state:'HOLD_CHECKS_PENDING',checks:active.length,statuses:contexts.size,failed,pending};
 if(!active.length&&!contexts.size)return{state:'HOLD_NO_CHECK_EVIDENCE',checks:0,statuses:0,failed:[],pending:[]};
 return{state:'CHECKS_REPORTED_SUCCESS',checks:active.length,statuses:contexts.size,failed:[],pending:[]};
}
function disposition(pr,summary){
 if(!pr)return'NO_FORMIC_PR';
 if(pr.merged_at)return'MERGED_EXTERNALLY_OBSERVED';
 if(pr.state==='closed')return'HOLD_CLOSED_PR_RETRY_SUPPRESSED';
 if(!pr.draft)return'HOLD_NON_DRAFT_PR';
 if(summary.state==='CHECKS_REPORTED_SUCCESS')return'REVIEW_READY_NO_AUTO_MERGE';
 return summary.state;
}
function stablePublicMetadata(pr){
 if(!pr)return null;
 return{number:pr.number,url:pr.html_url,state:pr.state,draft:pr.draft,merged:!!pr.merged_at,headSha:pr.head?.sha||null,baseBranch:pr.base?.ref||null};
}
async function gitApi(route,token){
 const headers={'Accept':'application/vnd.github+json','User-Agent':'jane-formic-b162','X-GitHub-Api-Version':'2022-11-28'};
 if(token)headers.Authorization='Bearer '+token;
 const response=await fetch('https://api.github.com'+route,{method:'GET',headers});
 if(!response.ok)throw Error('HTTP '+response.status+' '+route.split('?')[0]);
 return response.json();
}
const enc=encodeURIComponent;
async function inspect(repo,token){
 const prefix='/repos/'+repo.full_name;
 const prs=await gitApi(prefix+'/pulls?state=all&head='+enc(OWNER+':'+BRANCH)+'&per_page=100&sort=created&direction=desc',token);
 if(!Array.isArray(prs))throw Error('INVALID_PULL_REQUESTS');
 // Fail closed if PR history pagination would be incomplete.
 if(prs.length===100)return{repo:repo.full_name,decision:'HOLD_PR_HISTORY_TRUNCATED'};
 if(!prs.length)return{repo:repo.full_name,decision:'NO_FORMIC_PR',candidate:true};
 const pr=prs[0],prInfo=stablePublicMetadata(pr);
 if(!prInfo?.number||!prInfo.headSha)return{repo:repo.full_name,decision:'HOLD_INVALID_PR_DATA',pr:prInfo};
 if(pr.state!=='open'||pr.merged_at||!pr.draft){
  return{repo:repo.full_name,decision:disposition(pr,{}),pr:prInfo,checks:{state:'NOT_NEEDED'},suppression:pr.state==='closed'&&!pr.merged_at};
 }
 const sha=enc(pr.head.sha);
 // If a check endpoint is forbidden or temporarily unavailable, report HOLD, never assume green.
 const results=await Promise.allSettled([
  gitApi(prefix+'/commits/'+sha+'/check-runs?per_page=100',token),
  gitApi(prefix+'/commits/'+sha+'/status',token)
 ]);
 const checks=results[0].status==='fulfilled'?results[0].value:null;
 const status=results[1].status==='fulfilled'?results[1].value:null;
 if(checks&&checks.total_count>100)return{repo:repo.full_name,decision:'HOLD_CHECKS_TRUNCATED',pr:prInfo};
 const summary=checkSummary(checks?.check_runs||[],status?.statuses||[],
 {checksAccessible:results[0].status==='fulfilled',statusesAccessible:results[1].status==='fulfilled'});
 return{repo:repo.full_name,decision:disposition(pr,summary),pr:prInfo,checks:summary,suppression:summary.state==='HOLD_CHECKS_FAILED'};
}
function classifyLedger(rows){
 const summary={observed:rows.length,reviewReady:0,failed:0,pending:0,closedSuppressed:0,notYetProposed:0,hold:0};
 for(const r of rows){
  if(r.decision==='REVIEW_READY_NO_AUTO_MERGE')summary.reviewReady++;
  else if(r.decision==='HOLD_CHECKS_FAILED')summary.failed++;
  else if(r.decision==='HOLD_CHECKS_PENDING')summary.pending++;
  else if(r.decision==='HOLD_CLOSED_PR_RETRY_SUPPRESSED')summary.closedSuppressed++;
  else if(r.decision==='NO_FORMIC_PR')summary.notYetProposed++;
  else if(r.decision.startsWith('HOLD'))summary.hold++;
 }
 return summary;
}
async function run({repos,token='',maxTargets=MAX_TARGETS,inspectFn=inspect,policyFn=readPolicy}={}){
 if(!Array.isArray(repos)||!Number.isInteger(maxTargets)||maxTargets<1||maxTargets>MAX_TARGETS)throw Error('INVALID_SCAN_INPUT');
 const rows=[];
 for(const repo of repos){
  if(rows.length>=maxTargets)break;
  if(repoGate(repo)!=='ELIGIBLE')continue;
  let policy;
  try{policy=await policyFn(repo,token)}catch(e){rows.push({repo:repo.full_name,decision:'HOLD_POLICY_FETCH_FAILED',error:String(e.message).slice(0,110)});continue}
  if(policyGate(policy)!=='ELIGIBLE')continue;
  try{rows.push(await inspectFn(repo,token))}catch(e){rows.push({repo:repo.full_name,decision:'HOLD_INSPECTION_FAILED',error:String(e.message).slice(0,110)})}
 }
 return{schema:'JANE-B162-FORMIC-PR-VERIFICATION-v1',owner:OWNER,observedAt:new Date().toISOString(),mode:'READ_ONLY',results:rows,summary:classifyLedger(rows),governance:{sourceWitnesses:['a1','b1','c1'],observerDepth:1,isaDefined:false,noQuorum:true,automaticMerges:false,defaultBranchWrites:false,physicalPromotion:false},warnings:['REPORTS_ARE_PER_RUN_IMMUTABLE_ARTIFACTS','NOT_A_COMPLETE_ACCOUNT_SCAN_IF_BOUNDED','NO_CHECK_RESULTS_IS_HOLD']};
}
async function main(){
 const args=process.argv.slice(2);
 const out=args.includes('--output')?args[args.indexOf('--output')+1]:'ecosystem/reports/b162-latest.json';
 const token=process.env.FORMIC_READ_TOKEN||process.env.GITHUB_TOKEN||'';
 const repos=await publicRepos(token);
 const report=await run({repos,token});
 fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({mode:'READ_ONLY',summary:report.summary}));
}
if(require.main===module)main().catch(e=>{console.error('HOLD '+e.message);process.exitCode=1});
module.exports={checkSummary,disposition,stablePublicMetadata,classifyLedger,inspect,run,gitApi};
