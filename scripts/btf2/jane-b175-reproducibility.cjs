'use strict';
/**
 * B175 — repeat B174 twice in independent disposable workspaces.
 * Reproducibility is observed, never a quorum or authorization.
 * No remote mutations and no target repository script execution.
 */
const crypto=require('node:crypto');
const {evaluate:auditTreeRun,audit:verifyManifest}=require('./jane-b174-tree-diff.cjs');
const SCHEMA='JANE-B175-REPRODUCIBILITY-v1';
const sha=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const allowedTarget='.github/ISSUE_TEMPLATE/bug_report.md';
const LIMIT=8;
function reject(reason,proof){
 return{schema:SCHEMA,status:'HOLD',reasons:[reason],repository:proof?.envelope?.repository??null,
  proposalSha256:proof?.sha256??null,repeats:2,sourceManifests:[],comparisonDigest:null,
  independentWorkspaces:false,codeExecutedFromTarget:false,mayCreatePR:false,
  mayRetry:false,mayMerge:false,mayWriteDefaultBranch:false};
}
function comparable(run){
 if(verifyManifest(run).status!=='PASS')throw Error('MANIFEST_AUDIT_FAILED');
 if(run.temporaryWorkspaceRemoved!==true)throw Error('UNCLEANED_WORKSPACE');
 const {repository,proposalSha256,baseSha,sourceTreeSha,before,after,delta}=run;
 return{repository,proposalSha256,baseSha,sourceTreeSha,before,after,delta};
}
function compare(first,second,proof){
 if(first?.status!=='EXACT_ONE_FILE_ADDITION'||second?.status!=='EXACT_ONE_FILE_ADDITION')
  return reject('REPEAT_DID_NOT_PASS',proof);
 let a,b;
 try{a=comparable(first);b=comparable(second)}
 catch(e){return reject(String(e.message).slice(0,100),proof)}
 if(a.repository!==proof?.envelope?.repository||a.proposalSha256!==proof?.sha256||
   a.baseSha!==proof?.envelope?.base?.commitSha)
  return reject('PROPOSAL_SCOPE_MISMATCH',proof);
 if(a.delta.additions.length!==1||a.delta.additions[0].path!==allowedTarget||
   a.delta.modifications.length!==0||a.delta.deletions.length!==0)
  return reject('UNEXPECTED_DELTA',proof);
 const aHash=sha(a),bHash=sha(b);
 if(aHash!==bHash)return{...reject('NONDETERMINISTIC_MANIFEST',proof),
   comparisonDigest:sha({first:aHash,second:bHash}),sourceManifests:[first.manifestSha256,second.manifestSha256]};
 const data={schema:SCHEMA,status:'REPRODUCIBLE_TREE_DELTA_NO_EXECUTION',
  reasons:[],repository:a.repository,proposalSha256:a.proposalSha256,baseSha:a.baseSha,
  sourceTreeSha:a.sourceTreeSha,repeats:2,sourceManifests:[first.manifestSha256,second.manifestSha256],
  normalizedManifestSha256:aHash,comparisonDigest:sha({first:aHash,second:bHash}),
  identicalBefore:true,identicalAfter:true,identicalAllowedDelta:true,
  independentWorkspaces:true,codeExecutedFromTarget:false,repoCiExecuted:false,
  mayCreatePR:false,mayRetry:false,mayMerge:false,mayWriteDefaultBranch:false};
 return{...data,attestationSha256:sha(data)};
}
function evaluate(inputs,{repeatFn=auditTreeRun}={}){
 const first=repeatFn(inputs);
 const second=repeatFn(inputs);
 return compare(first,second,inputs?.proof);
}
function audit(record){
 if(record?.schema!==SCHEMA||record.status!=='REPRODUCIBLE_TREE_DELTA_NO_EXECUTION'||
   record.repeats!==2||record.identicalBefore!==true||record.identicalAfter!==true||
   record.identicalAllowedDelta!==true||record.independentWorkspaces!==true||
   record.codeExecutedFromTarget!==false||record.repoCiExecuted!==false||
   record.mayCreatePR!==false||record.mayRetry!==false||record.mayMerge!==false||
   record.mayWriteDefaultBranch!==false)return{status:'HOLD',reason:'BOUNDARY'};
 const {attestationSha256,...body}=record;
 return attestationSha256===sha(body)?{status:'PASS',digest:attestationSha256}:{status:'HOLD',reason:'DIGEST'};
}
function registry(results){
 if(!Array.isArray(results)||results.length>LIMIT)throw Error('B175_RECORD_LIMIT');
 return{schema:'JANE-B175-REPRODUCIBILITY-REGISTRY-v1',mode:'READ_ONLY',
  status:results.length?'OBSERVATIONS_RECORDED':'HOLD_NO_PROPOSALS',results,
  counts:{observed:results.length,reproducible:results.filter(x=>x.status==='REPRODUCIBLE_TREE_DELTA_NO_EXECUTION').length,
   held:results.filter(x=>x.status==='HOLD').length},
  governance:{witnesses:['a1','b1','c1'],observerDepth:1,noQuorum:true,isaDefined:false,
   automaticWrites:false,automaticMerges:false,targetRepositoryCodeExecuted:false}};
}
module.exports={SCHEMA,compare,comparable,evaluate,audit,registry,reject};
