'use strict';
/**
 * B172: controlled Git patch-application integration, not target repository CI.
 * Consumes B168+B169+B170+B171, fails closed, never writes to a GitHub repo.
 */
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const {audit:proofAudit}=require('./jane-b168-proof-proposal.cjs');
const {audit:tripleAudit}=require('./jane-b171-triple-evidence.cjs');
const {TARGET,TEMPLATE}=require('./jane-b161-formic-agent.cjs');
const {digest}=require('./jane-b170-isolated-evaluation.cjs');
const SCHEMA='JANE-B172-CONTROLLED-INTEGRATION-v1';
function stopped(reason,proposal=null){return{schema:SCHEMA,status:'HOLD',reason,
 repository:proposal?.envelope?.repository||null,proposalSha256:proposal?.sha256||null,
 patchApplied:false,scratchGitChecksPassed:false,targetRepoCiExecuted:false,
 ownerAuthorized:false,mayCreatePR:false,mayMerge:false,mayRetry:false,
 scratchRemoved:false,mode:'SCRATCH_GIT_ONLY'};}
function verifyInputs({proposal,base,local,triple}){
 const reasons=[];
 if(proofAudit(proposal).status!=='PASS')reasons.push('B168_PROOF_INVALID');
 if(tripleAudit(triple).status!=='PASS')reasons.push('B171_EVIDENCE_INVALID');
 const e=proposal?.envelope;
 if(!e||!Array.isArray(e.proposal?.changes)||e.proposal.changes.length!==1)
   reasons.push('DIFF_NOT_SINGLE_CHANGE');
 if(base?.status!=='BASE_OBSERVED_PASS_NOT_PROPOSAL_VALIDATED'||
    local?.status!=='LOCAL_CHECKS_PASS')reasons.push('B169_OR_B170_NOT_PASS');
 if(triple?.proposalSha256!==proposal?.sha256||
   base?.proposalSha256!==proposal?.sha256||
   local?.proposalSha256!==proposal?.sha256)reasons.push('DIGEST_MISMATCH');
 if(triple?.repository!==e?.repository||base?.repository!==e?.repository||
   local?.repository!==e?.repository)reasons.push('REPOSITORY_MISMATCH');
 const sha=e?.base?.commitSha;
 if(triple?.baseSha!==sha||base?.baseSha!==sha||base?.observedSha!==sha||local?.baseSha!==sha)
   reasons.push('BASE_REVISION_MISMATCH');
 if(triple?.witnesses?.a1?.audited!==true||triple?.witnesses?.b1?.status!=='BASE_OBSERVED_PASS_NOT_PROPOSAL_VALIDATED'||
   triple?.witnesses?.c1?.status!=='LOCAL_CHECKS_PASS')reasons.push('WITNESS_MISMATCH');
 if(base?.proposalChecksExecuted!==false||local?.githubCiObserved!==false||
   triple?.safety?.proposalRepoCIExecuted!==false)reasons.push('INVALID_CI_CLAIM');
 if(e?.proposal?.changes?.[0]?.path!==TARGET||
   e?.proposal?.changes?.[0]?.after!==TEMPLATE)reasons.push('UNTRUSTED_PATCH');
 return [...new Set(reasons)];
}
function git(cwd,args,options={}){
 const result=spawnSync('git',args,{cwd,encoding:'utf8',timeout:8000,
   maxBuffer:131072,env:{PATH:process.env.PATH||'',HOME:cwd,GIT_CONFIG_NOSYSTEM:'1',
     GIT_CONFIG_GLOBAL:'/dev/null'},...options});
 if(result.error||result.status!==0)return{ok:false,detail:(result.stderr||result.error?.message||'git failed').slice(0,150)};
 return{ok:true};
}
function integrate({proposal,base,local,triple},{workspaceRoot=os.tmpdir(),gitFn=git}={}){
 const reasons=verifyInputs({proposal,base,local,triple});
 if(reasons.length)return stopped(reasons.join(','),proposal);
 let scratch,removed=false,result=stopped('UNKNOWN',proposal);
 try{
  scratch=fs.mkdtempSync(path.join(workspaceRoot,'jane-b172-'));
  const patch=proposal.envelope.proposal.changes[0].unifiedDiff;
  const patchPath=path.join(scratch,'change.patch');
  fs.writeFileSync(patchPath,patch,{encoding:'utf8',flag:'wx',mode:0o600});
  const init=gitFn(scratch,['init','--quiet']);
  if(!init.ok){result.reason='GIT_INIT_FAILED';return result}
  const check=gitFn(scratch,['apply','--check','--',patchPath]);
  if(!check.ok){result.reason='SCRATCH_APPLY_CHECK_FAILED';return result}
  const apply=gitFn(scratch,['apply','--',patchPath]);
  if(!apply.ok){result.reason='SCRATCH_APPLY_FAILED';return result}
  const target=path.join(scratch,TARGET);
  if(!fs.existsSync(target)){result.reason='TARGET_MISSING_AFTER_APPLY';return result}
  const actual=fs.readFileSync(target,'utf8');
  if(actual!==TEMPLATE||digest(actual)!==proposal.envelope.proposal.changes[0].afterSha256){
   result.reason='APPLIED_PATCH_BYTES_MISMATCH';return result
  }
  const status=gitFn(scratch,['status','--porcelain','--untracked-files=all']);
  if(!status.ok){result.reason='SCRATCH_STATUS_FAILED';return result}
  result={schema:SCHEMA,status:'SCRATCH_GIT_PATCH_PASS',reason:null,
   repository:proposal.envelope.repository,proposalSha256:proposal.sha256,
   baseSha:proposal.envelope.base.commitSha,patchApplied:true,scratchGitChecksPassed:true,
   checks:['GIT_INIT','GIT_APPLY_CHECK','GIT_APPLY','EXACT_PATCH_BYTES','PATCH_SHA256','GIT_STATUS'].map(name=>({name,status:'PASS'})),
   targetRepoCiExecuted:false,targetRepoCodeExecuted:false,ownerAuthorized:false,
   mayCreatePR:false,mayMerge:false,mayRetry:false,mode:'SCRATCH_GIT_ONLY',scratchRemoved:false};
 }catch{result.reason='SCRATCH_INTEGRATION_ERROR';result.status='HOLD'}
 finally{
  if(scratch){
   try{fs.rmSync(scratch,{recursive:true,force:true});removed=true}catch{result.status='HOLD';result.reason='SCRATCH_CLEANUP_FAILED'}
  }
  result.scratchRemoved=removed;
 }
 return result;
}
function report(items){
 if(!Array.isArray(items)||items.length>8)throw Error('TOO_MANY_ITEMS');
 return{schema:'JANE-B172-INTEGRATION-REPORT-v1',mode:'SCRATCH_GIT_ONLY',results:items,
  counts:{observed:items.length,passed:items.filter(x=>x.status==='SCRATCH_GIT_PATCH_PASS').length,
    held:items.filter(x=>x.status==='HOLD').length},
  governance:{observerDepth:1,witnesses:['a1','b1','c1'],noQuorum:true,
   isaDefined:false,automaticWrites:false,automaticMerge:false,
   actualTargetRepoCIExecuted:false,authorizesNewPR:false}};
}
module.exports={SCHEMA,verifyInputs,integrate,report,stopped};
