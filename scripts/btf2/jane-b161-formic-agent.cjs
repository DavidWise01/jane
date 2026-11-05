'use strict';
const fs=require('node:fs'),path=require('node:path');
const OWNER='DavidWise01';
const POLICY='.formic/policy.json';
const TARGET='.github/ISSUE_TEMPLATE/bug_report.md';
const BRANCH='formic/b161-bug-report';
const TEMPLATE=['---','name: Bug report','about: Report a reproducible defect','title: ""','labels: bug','assignees: ""','---','','## Description','Describe the problem.','','## Steps to reproduce','1.','2.','3.','','## Expected behavior','What should have happened?','','## Actual behavior','What happened instead?','','## Environment','- Version or commit:','- Operating system:','- Browser/runtime (if relevant):','','## Supporting evidence','Remove secrets, credentials, and personal information before attaching logs.',''].join('\n');
function scoped(full){return typeof full==='string'&&/^DavidWise01\/[A-Za-z0-9_.-]+$/.test(full)}
function repoGate(r){
 if(!r||!scoped(r.full_name))return'HOLD_OUT_OF_SCOPE';
 if(r.private||r.visibility==='private')return'HOLD_PRIVATE';
 if(r.archived||r.disabled||r.fork)return'HOLD_ARCHIVED_DISABLED_OR_FORK';
 if(!r.default_branch)return'HOLD_DEFAULT_BRANCH';
 return'ELIGIBLE';
}
function policyGate(p){
 if(!p||p.schema!=='FORMIC-REPO-POLICY-v1')return'HOLD_MISSING_POLICY';
 if(p.enabled!==true)return'HOLD_NOT_OPTED_IN';
 if(!Array.isArray(p.allowed_repairs)||!p.allowed_repairs.includes('BUG_REPORT_TEMPLATE'))return'HOLD_REPAIR_NOT_ALLOWED';
 if(p.max_open_pull_requests!==1)return'HOLD_LIMIT_POLICY';
 return'ELIGIBLE';
}
function decide(repo,policy,{fileExists=false,prExists=false,branchExists=false}={}){
 for(const x of [repoGate(repo),policyGate(policy)])if(x!=='ELIGIBLE')return{repo:repo?.full_name||null,decision:x};
 if(fileExists)return{repo:repo.full_name,decision:'NO_CHANGE_FILE_EXISTS'};
 if(prExists)return{repo:repo.full_name,decision:'NO_CHANGE_PR_EXISTS'};
 if(branchExists)return{repo:repo.full_name,decision:'HOLD_BRANCH_EXISTS'};
 return{repo:repo.full_name,decision:'PROPOSE_DRAFT_PR',path:TARGET,branch:BRANCH};
}
async function api(route,token,{method='GET',body,optional=false}={}){
 const url='https://api.github.com'+route;
 const headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'jane-formic-b161'};
 if(token)headers.Authorization='Bearer '+token;
 if(body!==undefined)headers['Content-Type']='application/json';
 const response=await fetch(url,{method,headers,body:body===undefined?undefined:JSON.stringify(body)});
 if(response.status===404&&optional)return null;
 if(!response.ok)throw Error('GitHub HTTP '+response.status+' '+method+' '+route.split('?')[0]);
 return response.status===204?{}:response.json();
}
const q=s=>encodeURIComponent(s);
async function publicRepos(token,maxPages=30){
 const arr=[];
 for(let page=1;page<=maxPages;page++){
  const result=await api('/users/'+OWNER+'/repos?per_page=100&page='+page+'&type=owner&sort=full_name&direction=asc',token);
  if(!Array.isArray(result))throw Error('INVALID_LIST');
  arr.push(...result);
  if(result.length<100)break;
 }
 return arr;
}
async function readPolicy(repo,token){
 const c=await api('/repos/'+repo.full_name+'/contents/'+POLICY+'?ref='+q(repo.default_branch),token,{optional:true});
 if(!c||c.encoding!=='base64'||c.size>12000)return null;
 try{return JSON.parse(Buffer.from(c.content,'base64').toString('utf8'))}catch{return null}
}
async function presence(repo,token){
 const prefix='/repos/'+repo.full_name;
 const [file,branch,prs]=await Promise.all([
  api(prefix+'/contents/'+TARGET+'?ref='+q(repo.default_branch),token,{optional:true}),
  api(prefix+'/git/ref/heads/'+BRANCH,token,{optional:true}),
  api(prefix+'/pulls?state=open&head='+q(OWNER+':'+BRANCH)+'&per_page=5',token)
 ]);
 return{fileExists:!!file,branchExists:!!branch,prExists:prs.length>0};
}
async function propose(repo,token){
 if(repoGate(repo)!=='ELIGIBLE')return{repo:repo.full_name,decision:repoGate(repo)};
 const policy=await readPolicy(repo,token);
 if(policyGate(policy)!=='ELIGIBLE')return{repo:repo.full_name,decision:policyGate(policy)};
 const p=await presence(repo,token),choice=decide(repo,policy,p);
 if(choice.decision!=='PROPOSE_DRAFT_PR')return choice;
 const prefix='/repos/'+repo.full_name;
 const base=await api(prefix+'/git/ref/heads/'+q(repo.default_branch),token);
 if(!base?.object?.sha)return{repo:repo.full_name,decision:'HOLD_NO_BASE_SHA'};
 await api(prefix+'/git/refs',token,{method:'POST',body:{ref:'refs/heads/'+BRANCH,sha:base.object.sha}});
 await api(prefix+'/contents/'+TARGET,token,{method:'PUT',body:{message:'docs(formic): add reproducible bug report issue template',content:Buffer.from(TEMPLATE,'utf8').toString('base64'),branch:BRANCH}});
 const pr=await api(prefix+'/pulls',token,{method:'POST',body:{title:'docs(formic): add bug report template',base:repo.default_branch,head:BRANCH,draft:true,body:'FORMIC B161: this repository explicitly opted in through .formic/policy.json. A documentation-only change is proposed for review. No automatic merge or default-branch write.'}});
 return{repo:repo.full_name,decision:'DRAFT_PR_OPENED',url:pr.html_url,number:pr.number};
}
async function main(){
 const args=process.argv.slice(2),fixture=args.includes('--fixture'),write=args.includes('--apply')&&process.env.FORMIC_ENABLE_PR_CREATION==='true'&&!fixture;
 const output=args.includes('--output')?args[args.indexOf('--output')+1]:'ecosystem/reports/b161-latest.json';
 const token=process.env.FORMIC_REPO_TOKEN||process.env.GITHUB_TOKEN||'';
 const records=[];
 if(fixture){
  const i=args.indexOf('--fixture'),source=args[i+1];if(!source)throw Error('MISSING_FIXTURE');
  for(const row of JSON.parse(fs.readFileSync(source,'utf8')).slice(0,3))records.push(decide(row.repo,row.policy,row.presence));
 }else{
  const repos=await publicRepos(token);
  // Filter first, then check explicit target opt-in before considering changes.
  for(const repo of repos){
   if(repoGate(repo)!=='ELIGIBLE')continue;
   const policy=await readPolicy(repo,token);
   if(policyGate(policy)!=='ELIGIBLE')continue;
   if(records.length>=3)break;
   try{
    if(write)records.push(await propose(repo,process.env.FORMIC_REPO_TOKEN));
    else records.push(decide(repo,policy,await presence(repo,token)));
   }catch(e){records.push({repo:repo.full_name,decision:'HOLD_API_FAILURE',reason:String(e.message).slice(0,160)})}
  }
 }
 const data={schema:'JANE-B161-FORMIC-PR-v1',owner:OWNER,mode:write?'OPT_IN_DRAFT_PR':'DRY_RUN',observedAt:new Date().toISOString(),results:records,governance:{maxTargetRepos:3,isaDefined:false,noQuorum:true,defaultBranchWrites:false,automaticMerge:false}};
 fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(data,null,2)+'\n');
 process.stdout.write(JSON.stringify({mode:data.mode,checked:records.length,opened:records.filter(x=>x.decision==='DRAFT_PR_OPENED').length})+'\n');
}
if(require.main===module)main().catch(e=>{process.stderr.write('HOLD '+e.message+'\n');process.exitCode=1});
module.exports={OWNER,POLICY,TARGET,BRANCH,TEMPLATE,scoped,repoGate,policyGate,decide,publicRepos,readPolicy,presence,propose};
