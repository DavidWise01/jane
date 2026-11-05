'use strict';
/**
 * B166: GET-only provenance retrieval for a versioned retry intent.
 * This is evidence gathering; no authorization to retry, merge or write.
 */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {versionedHistory}=require('./jane-b164-durable-repair.cjs');
const {validateIntent,ledger,audit,hash}=require('./jane-b165-owner-intent.cjs');
const {publicRepos,repoGate,policyGate,readPolicy,BRANCH}=require('./jane-b161-formic-agent.cjs');
const OWNER='DavidWise01',INTENT_PATH='.formic/retry-intent.json',MAX_TARGETS=8;
const enc=encodeURIComponent;
function scoped(name){return typeof name==='string'&&/^DavidWise01\/[A-Za-z0-9_.-]+$/.test(name)}
function blobSha(content){const bytes=Buffer.from(content,'utf8');return crypto.createHash('sha1').update(Buffer.from('blob '+bytes.length+'\0')).update(bytes).digest('hex')}
async function api(route,token,{optional=false}={}){
 const headers={Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'jane-b166-live-provenance'};
 if(token)headers.Authorization='Bearer '+token;
 const response=await fetch('https://api.github.com'+route,{method:'GET',headers});
 if(optional&&response.status===404)return null;
 if(!response.ok)throw Error('HTTP_'+response.status);
 return response.json();
}
function resolveAttestation(repo,content,commits,detail,nowIso){
 if(!scoped(repo?.full_name)||typeof repo?.default_branch!=='string'||!content||!Array.isArray(commits)||!detail)
  return{status:'HOLD',reason:'INCOMPLETE_DEFAULT_BRANCH_EVIDENCE'};
 if(content.type!=='file'||content.path!==INTENT_PATH||content.encoding!=='base64'||content.size>12000||
    typeof content.content!=='string')return{status:'HOLD',reason:'INVALID_CONTENTS_METADATA'};
 let raw,intent;
 try{raw=Buffer.from(content.content.replace(/\s/g,''),'base64').toString('utf8');intent=JSON.parse(raw)}
 catch{return{status:'HOLD',reason:'MALFORMED_INTENT'}};
 if(Buffer.byteLength(raw,'utf8')!==content.size||blobSha(raw)!==content.sha)return{status:'HOLD',reason:'GIT_BLOB_MISMATCH'};
 if((!commits.length||commits.length>2)||!commits[0]?.sha||detail.sha!==commits[0].sha)return{status:'HOLD',reason:'HISTORY_TRUNCATED_OR_UNPINNED'};
 const fileChanges=detail.files;
 if(!Array.isArray(fileChanges)||!fileChanges.some(f=>f.filename===INTENT_PATH&&['added','modified'].includes(f.status)&&f.sha===content.sha))
  return{status:'HOLD',reason:'UNVERIFIED_INTENT_PATH_CHANGE'};
 const ver=detail.commit?.verification;
 if(!ver||ver.verified!==true)return{status:'HOLD',reason:'UNVERIFIED_COMMIT'};
 const author=detail.author?.login,committer=detail.committer?.login;
 if(author!==OWNER||committer!==OWNER)return{status:'HOLD',reason:'ACCOUNT_ATTRIBUTION_MISMATCH'};
 if(!Number.isFinite(Date.parse(nowIso)))return{status:'HOLD',reason:'INVALID_CLOCK'};
 return{status:'EVIDENCE_PRESENT',intent,attestation:{
   repository:repo.full_name,path:INTENT_PATH,ref:repo.default_branch,default_branch:repo.default_branch,
   commit:{verification:{verified:true},author:{login:author},committer:{login:committer}},
   reviewedPolicyDigest:hash(intent),commitSha:detail.sha,blobSha:content.sha,
   provenanceLimit:'GitHub verification and account attribution do not prove human authorization'
 }};
}
async function examine(repo,nowIso,token,fetchFn=api){
 if(!scoped(repo?.full_name)||repoGate(repo)!=='ELIGIBLE')
  return{repository:repo?.full_name||'OUT_OF_SCOPE',status:'HOLD',reasons:['REPO_GATE']};
 const full=repo.full_name,base=repo.default_branch,root='/repos/'+full;
 // Only default-branch intent; never import arbitrary branch-supplied directives.
 const branch=await fetchFn(root+'/git/ref/heads/'+enc(base),token);
 const pinned=branch?.object?.sha;
 if(typeof pinned!=='string'||!/^[a-f0-9]{40}$/i.test(pinned))return{repository:full,status:'HOLD',reasons:['DEFAULT_REF_UNVERIFIED'],grantWriteAuthority:false};
 const content=await fetchFn(root+'/contents/'+INTENT_PATH+'?ref='+enc(pinned),token,{optional:true});
 if(!content)return{repository:full,status:'HOLD',reasons:['MISSING_INTENT'],grantWriteAuthority:false};
 const commits=await fetchFn(root+'/commits?path='+enc(INTENT_PATH)+'&sha='+enc(pinned)+'&per_page=2',token);
 if(!Array.isArray(commits)||commits.length!==1)
  return{repository:full,status:'HOLD',reasons:['HISTORY_INCOMPLETE_OR_CHANGED'],grantWriteAuthority:false};
 const detail=await fetchFn(root+'/commits/'+enc(commits[0].sha),token);
 const resolved=resolveAttestation(repo,content,commits,detail,nowIso);
 if(resolved.status!=='EVIDENCE_PRESENT')return{repository:full,status:'HOLD',reasons:[resolved.reason],grantWriteAuthority:false};
 const prs=await fetchFn(root+'/pulls?state=all&head='+enc(OWNER+':'+BRANCH)+'&per_page=100&sort=created&direction=desc',token);
 if(!Array.isArray(prs)||prs.length>=100)return{repository:full,status:'HOLD',reasons:['PR_HISTORY_INCOMPLETE'],grantWriteAuthority:false};
 let history;
 try{history=versionedHistory(full,prs,nowIso)}
 catch{return{repository:full,status:'HOLD',reasons:['INVALID_PR_HISTORY'],grantWriteAuthority:false}}
 // The B165 policy validator cannot read untrusted commit identities directly.
 return validateIntent(full,history,resolved.intent,resolved.attestation,nowIso);
}
async function observe({repos,token='',nowIso=new Date().toISOString(),maxTargets=MAX_TARGETS,policyFn=readPolicy,examineFn=examine}={}){
 if(!Number.isInteger(maxTargets)||maxTargets<1||maxTargets>MAX_TARGETS)throw Error('INVALID_TARGET_LIMIT');
 const list=repos||await publicRepos(token),reports=[];
 for(const repo of list){
  if(reports.length>=maxTargets)break;
  if(repoGate(repo)!=='ELIGIBLE')continue;
  let p;try{p=await policyFn(repo,token)}catch{continue}
  if(policyGate(p)!=='ELIGIBLE')continue;
  try{reports.push(await examineFn(repo,nowIso,token))}
  catch(e){reports.push({repository:repo.full_name,status:'HOLD',reasons:['GITHUB_READ_FAILURE'],grantWriteAuthority:false})}
 }
 return ledger(reports);
}
async function main(){
 const args=process.argv.slice(2),output=args.includes('--output')?args[args.indexOf('--output')+1]:'ecosystem/reports/b166-latest.json';
 const result=await observe({token:process.env.GITHUB_TOKEN||''});
 if(audit(result).status!=='PASS')throw Error('AUDIT_HOLD');
 fs.mkdirSync(path.dirname(output),{recursive:true});
 fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({status:'PASS',mode:'READ_ONLY',records:result.events.length,head:result.head}));
}
if(require.main===module)main().catch(e=>{console.error('HOLD '+e.message);process.exitCode=1});
module.exports={INTENT_PATH,MAX_TARGETS,blobSha,resolveAttestation,examine,observe,api};
