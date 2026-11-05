'use strict';
/**
 * B167: independent authorization-policy evidence for a versioned FORMIC repair.
 * GET-only. "POLICY_EVIDENCE_PRESENT" NEVER grants write, PR, or merge authority.
 */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {api,resolveAttestation,INTENT_PATH,blobSha}=require('./jane-b166-live-provenance.cjs');
const {validateIntent,hash}=require('./jane-b165-owner-intent.cjs');
const {versionedHistory}=require('./jane-b164-durable-repair.cjs');
const {publicRepos,repoGate,readPolicy,policyGate,BRANCH}=require('./jane-b161-formic-agent.cjs');
const OWNER='DavidWise01',APPROVAL_PATH='.formic/retry-authorization.json',MAX_TARGETS=8;
const REPAIR='BUG_REPORT_TEMPLATE',enc=encodeURIComponent;
const scoped=x=>typeof x==='string'&&/^DavidWise01\/[A-Za-z0-9_.-]+$/.test(x);
function decodeFile(file,expected){
 if(!file||file.type!=='file'||file.path!==expected||file.encoding!=='base64'||typeof file.content!=='string'||
    !Number.isInteger(file.size)||file.size<1||file.size>12000)return{status:'HOLD',reason:'FILE_METADATA'};
 let bytes,parsed;
 try{
  bytes=Buffer.from(file.content.replace(/\s/g,''),'base64');
  if(bytes.toString('base64')!==file.content.replace(/\s/g,''))throw Error('BAD_BASE64');
  if(bytes.length!==file.size||blobSha(bytes.toString('utf8'))!==file.sha)throw Error('BLOB_MISMATCH');
  parsed=JSON.parse(bytes.toString('utf8'));
 }catch{return{status:'HOLD',reason:'FILE_DECODE_OR_BLOB'}};
 return{status:'FILE_VERIFIED',value:parsed,blob:file.sha};
}
function evaluate({repo,intent,approval,provenance,history,defaultBranch,branchProtection,at}){
 const reasons=[];
 if(!scoped(repo))reasons.push('REPOSITORY_SCOPE');
 if(provenance?.status!=='OWNER_INTENT_EVIDENCE_PRESENT'||provenance?.grantWriteAuthority!==false)
  reasons.push('B166_PROVENANCE_NOT_ACCEPTED');
 if(!intent||intent.schema!=='FORMIC-RETRY-INTENT-v1'||intent.repository!==repo||intent.repair!==REPAIR)
  reasons.push('INTENT_SCOPE');
 if(!approval||approval.schema!=='FORMIC-RETRY-AUTHORIZATION-v1'||approval.enabled!==true||approval.repository!==repo||
    approval.repair!==REPAIR)reasons.push('AUTHORIZATION_FILE_SCOPE');
 if(!Number.isInteger(approval?.revision)||approval.revision<1)reasons.push('AUTHORIZATION_REVISION');
 if(!Number.isInteger(approval?.intent_revision)||approval.intent_revision!==intent?.revision)
  reasons.push('INTENT_REVISION_MISMATCH');
 if(!Number.isInteger(approval?.previous_pr)||approval.previous_pr!==intent?.previous_pr)
  reasons.push('PREVIOUS_PR_MISMATCH');
 if(typeof approval?.previous_head_sha!=='string'||approval.previous_head_sha!==intent?.previous_head_sha)
  reasons.push('PREVIOUS_HEAD_MISMATCH');
 if(typeof approval?.intent_digest!=='string'||approval.intent_digest!==hash(intent))
  reasons.push('INTENT_DIGEST_MISMATCH');
 if(!Array.isArray(approval?.allowed_actions)||approval.allowed_actions.length!==1||
    approval.allowed_actions[0]!=='REVIEW_FOR_DRAFT_PR')reasons.push('ACTION_NOT_NARROWLY_SCOPED');
 if(typeof approval?.expires_at!=='string'||!Number.isFinite(Date.parse(approval.expires_at))||
    !Number.isFinite(Date.parse(at))||Date.parse(approval.expires_at)<=Date.parse(at)||
    Date.parse(approval.expires_at)>Date.parse(at)+7*86400000)reasons.push('AUTHORIZATION_EXPIRY');
 if(!defaultBranch||approval?.default_branch!==defaultBranch)reasons.push('DEFAULT_BRANCH_MISMATCH');
 if(history?.disposition!=='COOLDOWN_ELAPSED_OWNER_RESET_REQUIRED')reasons.push('HISTORY_NOT_RECOVERABLE');
 // Branch protection can be inaccessible (403) or not configured (404); both HOLD.
 // Strict settings cannot substitute for owner consent, even if they exist.
 if(branchProtection?.enforce_admins?.enabled!==true||
   branchProtection?.required_pull_request_reviews?.required_approving_review_count<1)
   reasons.push('BRANCH_PROTECTION_NOT_VERIFIED');
 return{schema:'JANE-B167-REPAIR-AUTHORIZATION-EVIDENCE-v1',repository:repo,
  status:reasons.length?'HOLD':'POLICY_EVIDENCE_PRESENT',reasons:[...new Set(reasons)],
  action:'OBSERVE_ONLY',mayCreatePR:false,mayMerge:false,mayWriteDefaultBranch:false,mayRetry:false,
  humanAuthorizationVerified:false,isaDefined:false,noQuorum:true,
  interpretation:'POLICY_EVIDENCE_IS_NOT_HUMAN_AUTHENTICATION_OR_WRITE_PERMISSION'};
}
async function inspect(repo,nowIso,token,fetchFn=api){
 const full=repo?.full_name;
 if(repoGate(repo)!=='ELIGIBLE')return{repository:full||'unknown',status:'HOLD',reasons:['REPO_GATE'],mayCreatePR:false};
 const root='/repos/'+full,branch=repo.default_branch;
 const ref=await fetchFn(root+'/git/ref/heads/'+enc(branch),token);
 const pin=ref?.object?.sha;
 if(!/^[a-f0-9]{40}$/i.test(pin||''))return{repository:full,status:'HOLD',reasons:['DEFAULT_REF_UNPINNED'],mayCreatePR:false};
 const [intentFile,authFile]=await Promise.all([
  fetchFn(root+'/contents/'+INTENT_PATH+'?ref='+enc(pin),token,{optional:true}),
  fetchFn(root+'/contents/'+APPROVAL_PATH+'?ref='+enc(pin),token,{optional:true})
 ]);
 const i=decodeFile(intentFile,INTENT_PATH),a=decodeFile(authFile,APPROVAL_PATH);
 if(i.status!=='FILE_VERIFIED'||a.status!=='FILE_VERIFIED')
  return{repository:full,status:'HOLD',reasons:[i.reason||'',' '+(a.reason||'')].filter(Boolean),mayCreatePR:false};
 const [historyCommits,approvalCommits,historyPRs,protection]=await Promise.allSettled([
  fetchFn(root+'/commits?path='+enc(INTENT_PATH)+'&sha='+enc(pin)+'&per_page=2',token),
  fetchFn(root+'/commits?path='+enc(APPROVAL_PATH)+'&sha='+enc(pin)+'&per_page=2',token),
  fetchFn(root+'/pulls?state=all&head='+enc('DavidWise01:'+BRANCH)+'&per_page=100',token),
  fetchFn(root+'/branches/'+enc(branch)+'/protection',token)
 ]);
 if(historyCommits.status!=='fulfilled'||approvalCommits.status!=='fulfilled'||historyPRs.status!=='fulfilled'||protection.status!=='fulfilled'||
    !Array.isArray(historyCommits.value)||!historyCommits.value.length||
    !Array.isArray(approvalCommits.value)||!approvalCommits.value.length||
    !Array.isArray(historyPRs.value)||historyPRs.value.length>=100)
  return{repository:full,status:'HOLD',reasons:['LIVE_PROVENANCE_OR_PROTECTION_UNAVAILABLE'],mayCreatePR:false};
 const commits=historyCommits.value,detail=await fetchFn(root+'/commits/'+enc(commits[0].sha),token);
 const authDetail=await fetchFn(root+'/commits/'+enc(approvalCommits.value[0].sha),token);
 if(authDetail?.sha!==approvalCommits.value[0].sha||
    authDetail?.commit?.verification?.verified!==true||
    authDetail?.author?.login!==OWNER||authDetail?.committer?.login!==OWNER||
    !Array.isArray(authDetail?.files)||
    !authDetail.files.some(f=>f.filename===APPROVAL_PATH&&['added','modified'].includes(f.status)&&f.sha===a.blob))
   return{repository:full,status:'HOLD',reasons:['APPROVAL_COMMIT_UNVERIFIED'],mayCreatePR:false};
 const provenance=resolveAttestation(repo,intentFile,commits,detail,nowIso);
 if(provenance.status!=='EVIDENCE_PRESENT')
  return{repository:full,status:'HOLD',reasons:['B166_'+provenance.reason],mayCreatePR:false};
 let history;
 try{history=versionedHistory(full,historyPRs.value,nowIso)}
 catch{return{repository:full,status:'HOLD',reasons:['PR_TIMELINE_INVALID'],mayCreatePR:false}}
 const ownerEvidence=validateIntent(full,history,i.value,provenance.attestation,nowIso);
 return evaluate({repo:full,intent:i.value,approval:a.value,provenance:ownerEvidence,history,
  defaultBranch:branch,branchProtection:protection.value,at:nowIso});
}
async function scan({repos,token='',nowIso=new Date().toISOString(),policyFn=readPolicy,inspectFn=inspect,maxTargets=MAX_TARGETS}={}){
 if(!Number.isInteger(maxTargets)||maxTargets<1||maxTargets>MAX_TARGETS)throw Error('MAX_TARGETS');
 const targets=repos||await publicRepos(token),results=[];
 for(const r of targets){
  if(results.length>=maxTargets)break;
  if(repoGate(r)!=='ELIGIBLE')continue;
  try{
   const p=await policyFn(r,token);
   if(policyGate(p)!=='ELIGIBLE')continue;
   results.push(await inspectFn(r,nowIso,token));
  }catch{results.push({repository:r.full_name,status:'HOLD',reasons:['READ_FAILED'],mayCreatePR:false})}
 }
 return{schema:'JANE-B167-ACCOUNT-AUTHORITY-EVIDENCE-REPORT-v1',owner:OWNER,
   observedAt:nowIso,mode:'READ_ONLY',results,summary:{observed:results.length,evidencePresent:results.filter(x=>x.status==='POLICY_EVIDENCE_PRESENT').length,holds:results.filter(x=>x.status==='HOLD').length},
   governance:{automaticWrite:false,automaticRetry:false,automaticMerge:false,isaDefined:false,witnesses:['a1','b1','c1'],observerDepth:1,noQuorum:true}};
}
async function main(){
 const args=process.argv.slice(2),output=args.includes('--output')?args[args.indexOf('--output')+1]:'ecosystem/reports/b167-latest.json';
 const report=await scan({token:process.env.GITHUB_TOKEN||''});
 fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({mode:report.mode,summary:report.summary}));
}
if(require.main===module)main().catch(e=>{console.error('HOLD '+e.message);process.exitCode=1});
module.exports={OWNER,APPROVAL_PATH,decodeFile,evaluate,inspect,scan};
