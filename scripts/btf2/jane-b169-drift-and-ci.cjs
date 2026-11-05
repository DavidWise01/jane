'use strict';
/* B169: live, read-only, fail-closed base drift / CI observation for B168 proposals. */
const fs=require('node:fs');
const path=require('node:path');
const {audit:proofAudit}=require('./jane-b168-proof-proposal.cjs');
const OWNER='DavidWise01';
const MAX_PROPOSALS=8;
const shaPattern=/^[a-f0-9]{40}$/i;
const expectedStatus=new Set(['success','failure','error','pending']);
function classify(proof,{refSha=null,fileState='UNKNOWN',checks=null,statuses=null,checkRunsComplete=false,statusesComplete=false,readError=null}={}){
 const repo=proof?.envelope?.repository;
 const reasons=[];
 if(proofAudit(proof).status!=='PASS')reasons.push('PROOF_AUDIT_FAILED');
 const base=proof?.envelope?.base?.commitSha;
 if(!shaPattern.test(refSha||''))reasons.push('DEFAULT_REF_UNVERIFIED');
 else if(refSha!==base)reasons.push('BASE_SHA_DRIFT');
 if(fileState==='PRESENT')reasons.push('TARGET_ALREADY_EXISTS');
 else if(fileState!=='ABSENT')reasons.push('TARGET_PRESENCE_UNKNOWN');
 if(readError)reasons.push('GITHUB_READ_FAILED');
 if(checkRunsComplete!==true||statusesComplete!==true)reasons.push('CI_EVIDENCE_INCOMPLETE');
 if(!Array.isArray(checks)||!Array.isArray(statuses))reasons.push('CI_EVIDENCE_MISSING');
 let failed=[],pending=[],passed=[],observedCount=0;
 if(Array.isArray(checks)&&Array.isArray(statuses)){
  // A GitHub check run is identified by its app and name. Only the latest per identity is counted.
  const latest=new Map();
  for(const c of checks){
   if(!c||typeof c.name!=='string'||!c.name)continue;
   const key=String(c.app?.id??'')+'|'+c.name;
   const prev=latest.get(key),when=Date.parse(c.completed_at||c.started_at||c.created_at||0);
   const was=Date.parse(prev?.completed_at||prev?.started_at||prev?.created_at||0);
   if(!prev||Number.isFinite(when)&&(!Number.isFinite(was)||when>=was))latest.set(key,c);
  }
  const contexts=new Map();
  // Status endpoint lists newest first; keep the first status for each context.
  for(const c of statuses)if(typeof c?.context==='string'&&!contexts.has(c.context))contexts.set(c.context,c);
  observedCount=latest.size+contexts.size;
  for(const c of latest.values()){
   if(c.status!=='completed')pending.push('check:'+c.name);
   else if(c.conclusion==='success')passed.push('check:'+c.name);
   else if(c.conclusion==='neutral'||c.conclusion==='skipped')pending.push('check:'+c.name+':NOT_SUCCESS');
   else failed.push('check:'+c.name+':'+String(c.conclusion||'UNKNOWN'));
  }
  for(const c of contexts.values()){
   if(c.state==='success')passed.push('status:'+c.context);
   else if(c.state==='failure'||c.state==='error')failed.push('status:'+c.context+':'+c.state);
   else pending.push('status:'+c.context+':'+String(c.state||'UNKNOWN'));
  }
  if(observedCount===0)reasons.push('NO_BASE_CI_EVIDENCE');
  if(failed.length)reasons.push('BASE_CI_FAILED');
  if(pending.length)reasons.push('BASE_CI_UNRESOLVED');
 }
 const unique=[...new Set(reasons)];
 return{schema:'JANE-B169-DRIFT-AND-CI-v1',repository:repo||null,baseSha:base||null,observedSha:refSha,
  status:unique.length?'HOLD':'BASE_OBSERVED_PASS_NOT_PROPOSAL_VALIDATED',reasons:unique,
  evidence:{targetFileState:fileState,checkRuns:checks?.length??null,commitStatuses:statuses?.length??null,
    observedCount,failed,pending,passed},
  proposalChecksExecuted:false,proposalChecksPassed:false,mayCreatePR:false,mayRetry:false,mayMerge:false,
  mayWriteDefaultBranch:false,observationOnly:true,noQuorum:true,isaDefined:false};
}
const q=encodeURIComponent;
async function request(route,token,{optional=false}={}){
 const headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'jane-b169-base-verification'};
 if(token)headers.Authorization='Bearer '+token;
 const response=await fetch('https://api.github.com'+route,{method:'GET',headers});
 if(optional&&response.status===404)return null;
 if(!response.ok)throw Error('HTTP '+response.status+' '+route.split('?')[0]);
 return response.json();
}
async function inspect(proof,token='',requestFn=request){
 const scope=proof?.envelope?.repository;
 if(proofAudit(proof).status!=='PASS')return classify(proof,{readError:'INVALID_PROOF'});
 if(typeof scope!=='string'||!/^DavidWise01\/[A-Za-z0-9._-]+$/.test(scope))return classify(proof,{readError:'SCOPE'});
 const base=proof.envelope.base,expected=proof.envelope.proposal.changes[0];
 // Read and compare ref before AND after all evidence to detect mid-observation drift.
 const root='/repos/'+scope,refRoute=root+'/git/ref/heads/'+q(base.branch);
 try{
  const metadata=await requestFn(root,token);
  if(metadata?.full_name!==scope||metadata?.owner?.login!==OWNER||metadata?.private!==false||
     metadata?.archived===true||metadata?.disabled===true||metadata?.fork===true||
     metadata?.default_branch!==base.branch)
   return classify(proof,{readError:'REPOSITORY_SCOPE_OR_DEFAULT_BRANCH_CHANGED'});
  const first=await requestFn(refRoute,token);
  const firstSha=first?.object?.sha;
  if(!shaPattern.test(firstSha||'')||firstSha!==base.commitSha)return classify(proof,{refSha:firstSha,fileState:'UNKNOWN'});
  const [file,runResult,statusResult]=await Promise.allSettled([
   requestFn(root+'/contents/'+expected.path+'?ref='+q(firstSha),token,{optional:true}),
   requestFn(root+'/commits/'+q(firstSha)+'/check-runs?per_page=100',token),
   requestFn(root+'/commits/'+q(firstSha)+'/status',token)
  ]);
  const last=await requestFn(refRoute,token);
  const lastSha=last?.object?.sha;
  if(firstSha!==lastSha)return classify(proof,{refSha:lastSha,fileState:'UNKNOWN',readError:'REF_CHANGED_DURING_READ'});
  const state=file.status==='fulfilled'?(file.value===null?'ABSENT':'PRESENT'):'UNKNOWN';
  const cr=runResult.status==='fulfilled'?runResult.value:null;
  const st=statusResult.status==='fulfilled'?statusResult.value:null;
  const checksComplete=!!cr&&Array.isArray(cr.check_runs)&&Number.isInteger(cr.total_count)&&cr.total_count<=100&&cr.check_runs.length===cr.total_count;
  // Combined status payload includes total_count for statuses if available; if count is missing,
  // fail closed rather than claiming complete. Source API can truncate at 100.
  const statusesComplete=!!st&&Array.isArray(st.statuses)&&
   Number.isInteger(st.total_count)&&st.total_count<=100&&st.statuses.length===st.total_count;
  return classify(proof,{refSha:lastSha,fileState:state,checks:cr?.check_runs??null,
   statuses:st?.statuses??null,checkRunsComplete:checksComplete,statusesComplete,
   readError:[file,runResult,statusResult].some(x=>x.status==='rejected')?'ENDPOINT_UNAVAILABLE':null});
 }catch(e){return classify(proof,{readError:String(e.message).slice(0,80)})}
}
function report(records){
 if(!Array.isArray(records)||records.length>MAX_PROPOSALS)throw Error('INVALID_REPORT');
 return{schema:'JANE-B169-LIVE-DRIFT-REPORT-v1',mode:'READ_ONLY',owner:OWNER,observedAt:new Date().toISOString(),
  entries:records,counts:{observed:records.length,held:records.filter(x=>x.status==='HOLD').length,
    baseObservedPass:records.filter(x=>x.status==='BASE_OBSERVED_PASS_NOT_PROPOSAL_VALIDATED').length},
  governance:{observerDepth:1,witnesses:['a1','b1','c1'],noQuorum:true,isaDefined:false,
   proposalChecksExecuted:false,automaticWrites:false,automaticMerges:false}};
}
async function main(){
 const argv=process.argv.slice(2),i=argv.indexOf('--input'),o=argv.indexOf('--output');
 if(i<0||!argv[i+1])throw Error('INPUT_PROPOSAL_REQUIRED');
 const input=JSON.parse(fs.readFileSync(argv[i+1],'utf8'));
 const proposals=input?.schema==='JANE-B168-PROPOSAL-REGISTRY-v1'?input.entries:[input];
 if(!Array.isArray(proposals)||proposals.length>MAX_PROPOSALS)throw Error('INVALID_PROPOSAL_COUNT');
 const results=[];for(const x of proposals)results.push(await inspect(x,process.env.GITHUB_TOKEN||''));
 const output=report(results),target=o>=0?argv[o+1]:'ecosystem/reports/b169-latest.json';
 if(!target)throw Error('OUTPUT_PATH_REQUIRED');
 fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,JSON.stringify(output,null,2)+'\n');
 console.log(JSON.stringify({status:'OBSERVED',counts:output.counts,proposalsExecuted:0}));
}
if(require.main===module)main().catch(e=>{console.error('HOLD '+e.message);process.exitCode=1});
module.exports={classify,inspect,report,request};
