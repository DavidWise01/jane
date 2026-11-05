'use strict';
/**
 * B171: bind independent B168, B169, B170 evidence by exact digest and time.
 * Binding is evidence only, NEVER authority to execute, retry, open PR or merge.
 */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {audit:proofAudit}=require('./jane-b168-proof-proposal.cjs');
const {inspect:inspectBase}=require('./jane-b169-drift-and-ci.cjs');
const {examine:evaluatePatch}=require('./jane-b170-isolated-evaluation.cjs');
const ROOT='ecosystem/proposals',MAX=8,TTL_MS=5*60*1000;
const h=o=>crypto.createHash('sha256').update(JSON.stringify(o)).digest('hex');
const time=x=>typeof x==='string'&&Number.isFinite(Date.parse(x))?Date.parse(x):null;
function bind({proof,base,local,baseObservedAt,localEvaluatedAt,nowIso}){
 const reasons=[],now=time(nowIso),bAt=time(baseObservedAt),lAt=time(localEvaluatedAt);
 if(proofAudit(proof).status!=='PASS')reasons.push('PROOF_AUDIT_HOLD');
 if(!proof?.sha256||!/^[0-9a-f]{64}$/i.test(proof.sha256))reasons.push('PROPOSAL_SHA_MISSING');
 if(base?.schema!=='JANE-B169-DRIFT-AND-CI-v1'||base.status!=='BASE_OBSERVED_PASS_NOT_PROPOSAL_VALIDATED')
   reasons.push('B169_BASE_NOT_OBSERVED_PASS');
 if(local?.schema!=='JANE-B170-ISOLATED-REPAIR-EVALUATION-v1'||local.status!=='LOCAL_CHECKS_PASS'||
   local.localChecksPassed!==true||local.workspaceDeleted!==true||local.proposalTestsExecuted!==true)
   reasons.push('B170_LOCAL_VALIDATION_INCOMPLETE');
 if(base?.proposalSha256!==proof?.sha256||local?.proposalSha256!==proof?.sha256)
   reasons.push('EVIDENCE_PROPOSAL_DIGEST_MISMATCH');
 const repo=proof?.envelope?.repository,sha=proof?.envelope?.base?.commitSha;
 if(base?.repository!==repo||local?.repository!==repo||base?.baseSha!==sha||
   base?.observedSha!==sha||local?.baseSha!==sha)reasons.push('REPOSITORY_OR_BASE_SHA_MISMATCH');
 if(base?.proposalChecksExecuted!==false||base?.proposalChecksPassed!==false||
   local?.githubCiObserved!==false||local?.githubCiPassed!==false||
   local?.repositoryCodeExecuted!==false)reasons.push('EVIDENCE_TYPE_CONFUSED');
 if(base?.mayCreatePR!==false||base?.mayMerge!==false||base?.mayRetry!==false||
   local?.mayCreatePR!==false||local?.mayMerge!==false||local?.mayRetry!==false)
   reasons.push('UNEXPECTED_AUTHORITY');
 if(!Array.isArray(local?.checks)||local.checks.length!==7||!local.checks.every(x=>x.status==='PASS'))
   reasons.push('LOCAL_CHECK_SET_INCOMPLETE');
 if(now===null||bAt===null||lAt===null)reasons.push('TIME_EVIDENCE_MISSING');
 else if(bAt>now||lAt>now||now-bAt>TTL_MS||now-lAt>TTL_MS||Math.abs(bAt-lAt)>TTL_MS)
   reasons.push('EVIDENCE_STALE_OR_FUTURE');
 const unique=[...new Set(reasons)];
 const envelope={schema:'JANE-B171-TRIPLE-EVIDENCE-v1',
   status:unique.length?'HOLD':'EVIDENCE_BOUND_NO_EXECUTION',
   reasons:unique,repository:repo||null,proposalSha256:proof?.sha256||null,
   baseSha:sha||null,observation:{baseObservedAt:baseObservedAt||null,localEvaluatedAt:localEvaluatedAt||null,assembledAt:nowIso||null,ttlSeconds:300},
   witnesses:{
    a1:{type:'B168_PROOF',audited:proofAudit(proof).status==='PASS'},
    b1:{type:'B169_LIVE_BASE',status:base?.status||'MISSING',proposedDiffTested:false},
    c1:{type:'B170_LOCAL_PATCH',status:local?.status||'MISSING',githubCiPassed:false}
   },safety:{mayCreatePR:false,mayRetry:false,mayMerge:false,mayWriteDefaultBranch:false,
    proposalRepoCIExecuted:false,ownerAuthorizationEstablished:false},
   authority:'OBSERVATION_ONLY'};
 return{...envelope,evidenceDigest:h(envelope)};
}
function audit(record){
 if(!record||record.schema!=='JANE-B171-TRIPLE-EVIDENCE-v1'||!Array.isArray(record.reasons))return{status:'HOLD',reason:'SCHEMA'};
 const {evidenceDigest,...body}=record;
 if(h(body)!==evidenceDigest||body.status!=='EVIDENCE_BOUND_NO_EXECUTION'||body.reasons.length||
   body.safety?.mayCreatePR!==false||body.safety?.mayRetry!==false||
   body.safety?.mayMerge!==false||body.safety?.proposalRepoCIExecuted!==false||
   body.safety?.ownerAuthorizationEstablished!==false||body.authority!=='OBSERVATION_ONLY')
   return{status:'HOLD',reason:'DIGEST_OR_BOUNDARY'};
 return{status:'PASS',evidenceDigest};
}
function candidates(dir=ROOT){
 if(!fs.existsSync(dir))return[];
 const entries=fs.readdirSync(dir,{withFileTypes:true}).filter(x=>x.isFile()&&/^[A-Za-z0-9_.-]+[.]json$/.test(x.name)).map(x=>path.join(dir,x.name)).sort();
 if(entries.length>MAX)throw Error('TOO_MANY_PROPOSALS');
 return entries;
}
async function run({dir=ROOT,token='',now=()=>new Date().toISOString(),inspect=inspectBase,examine=evaluatePatch}={}){
 const results=[];
 for(const file of candidates(dir)){
  let proof;
  try{proof=JSON.parse(fs.readFileSync(file,'utf8'))}
  catch{results.push({schema:'JANE-B171-TRIPLE-EVIDENCE-v1',status:'HOLD',reasons:['INVALID_PROOF_FILE'],file:path.basename(file),safety:{mayCreatePR:false,mayRetry:false,mayMerge:false}});continue}
  const time0=now();
  let b,l;
  try{b=await inspect(proof,token)}
  catch{b={status:'HOLD',schema:'JANE-B169-DRIFT-AND-CI-v1'}}
  const time1=now();
  try{l=examine(proof)}
  catch{l={status:'HOLD',schema:'JANE-B170-ISOLATED-REPAIR-EVALUATION-v1'}}
  const time2=now();
  results.push(bind({proof,base:b,local:l,baseObservedAt:time1,localEvaluatedAt:time2,nowIso:time2}));
 }
 return{schema:'JANE-B171-EVIDENCE-REGISTRY-v1',mode:'READ_ONLY',
   status:results.length?'OBSERVATIONS_RECORDED':'HOLD_NO_PROPOSALS',
   entries:results,counts:{observed:results.length,bound:results.filter(x=>x.status==='EVIDENCE_BOUND_NO_EXECUTION').length,
    held:results.filter(x=>x.status==='HOLD').length},
   governance:{witnesses:['a1','b1','c1'],observerDepth:1,noQuorum:true,isaDefined:false,
    automaticWrites:false,autoMerge:false,proposalRepoCIExecuted:false}};
}
async function main(){
 const argv=process.argv.slice(2),i=argv.indexOf('--output'),out=i>=0?argv[i+1]:'ecosystem/reports/b171-latest.json';
 if(!out)throw Error('OUTPUT_REQUIRED');
 const r=await run({token:process.env.GITHUB_TOKEN||''});
 fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(r,null,2)+'\n');
 console.log(JSON.stringify({status:r.status,counts:r.counts,writeAuthority:false}));
}
if(require.main===module)main().catch(e=>{console.error('HOLD '+e.message);process.exitCode=1});
module.exports={TTL_MS,bind,audit,candidates,run};
