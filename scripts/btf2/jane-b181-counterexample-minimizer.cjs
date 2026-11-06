'use strict';
/**
 * B181: bounded, deterministic shrinking of real B180 parser disagreements.
 * No input hallucination. No target-repository code or GitHub writes.
 */
const crypto=require('node:crypto');
const {TEMPLATE}=require('./jane-b161-formic-agent.cjs');
const {parseTemplate}=require('./jane-b177-semantic-template.cjs');
const {parseIndependent}=require('./jane-b179-independent-parser.cjs');
const b180=require('./jane-b180-deterministic-fuzz.cjs');
const SCHEMA='JANE-B181-MINIMAL-COUNTEREXAMPLE-v1';
const MAX_STEPS=300,MAX_ITEMS=12,MAX_BYTES=9216,MAX_PREVIEW=320;
const digest=o=>crypto.createHash('sha256').update(JSON.stringify(o)).digest('hex');
const hash=s=>crypto.createHash('sha256').update(Buffer.from(s,'utf8')).digest('hex');
function observe(input,a,b){
 const x=b180.decision(a,input),y=b180.decision(b,input);
 return{first:{accepted:x.accept,error:x.error},second:{accepted:y.accept,error:y.error}};
}
function signature(observation){
 const {first,second}=observation;
 return JSON.stringify([first.accepted,first.error,second.accepted,second.error]);
}
function mismatch(o){return signature(o)!==JSON.stringify([o.first.accepted,o.first.error,o.first.accepted,o.first.error])}
function record(input){return{sha256:hash(input),bytes:Buffer.byteLength(input,'utf8'),preview:input.slice(0,MAX_PREVIEW)}}
function minimize(source,{first=parseTemplate,second=parseIndependent,maxSteps=MAX_STEPS}={}){
 if(typeof source!=='string'||Buffer.byteLength(source,'utf8')>MAX_BYTES||!Number.isInteger(maxSteps)||maxSteps<1||maxSteps>MAX_STEPS)
  return{status:'HOLD',reason:'INVALID_INPUT_OR_BUDGET'};
 const original=observe(source,first,second),fixed=signature(original);
 if(!mismatch(original))return{status:'HOLD',reason:'NO_ORIGINAL_DISAGREEMENT'};
 let current=source,steps=0,granularity=2;
 while(current.length>1&&steps<maxSteps){
  const chunk=Math.ceil(current.length/granularity);let reduced=false;
  for(let start=0;start<current.length&&steps<maxSteps;start+=chunk){
   const candidate=current.slice(0,start)+current.slice(start+chunk);
   steps++;
   if(candidate.length&&signature(observe(candidate,first,second))===fixed){
    current=candidate;granularity=Math.max(2,granularity-1);reduced=true;break;
   }
  }
  if(!reduced){
   if(granularity>=current.length)break;
   granularity=Math.min(current.length,granularity*2);
  }
 }
 const after=observe(current,first,second);
 if(signature(after)!==fixed||current.length>source.length)return{status:'HOLD',reason:'SHRINK_SIGNATURE_LOST'};
 return{status:'COUNTEREXAMPLE_MINIMIZED',original:record(source),minimized:record(current),
  originalInput:source,minimizedInput:current,originalDecision:original,minimizedDecision:after,
  signature:fixed,attempts:steps,limit:maxSteps,strictlySmaller:current.length<source.length,
  locallyMinimal:false,claim:'bounded delta debugging, not a proof of global minimality'};
}
function run({seed=b180.SEED,rounds=b180.ROUNDS,first=parseTemplate,second=parseIndependent}={}){
 const baseline=b180.run({seed,rounds,first,second});
 const generated=b180.reproducibleMutations({seed,rounds});
 const byId=new Map(generated.map(x=>[x.id,x.value]));
 const issues=[],examples=[];
 for(const issue of baseline.counterexamples.slice(0,MAX_ITEMS)){
  if(!byId.has(issue.id)){issues.push('COUNTEREXAMPLE_NOT_IN_GENERATOR:'+issue.id);continue}
  const input=byId.get(issue.id);
  if(hash(input)!==issue.inputSha256){issues.push('INPUT_HASH_MISMATCH:'+issue.id);continue}
  const minimized=minimize(input,{first,second});
  if(minimized.status!=='COUNTEREXAMPLE_MINIMIZED'){issues.push('SHRINK_FAILED:'+issue.id);continue}
  examples.push({id:issue.id,...minimized});
 }
 const empty=baseline.status==='DETERMINISTIC_FUZZ_AGREEMENT_NO_EXECUTION'&&baseline.counterexamples.length===0;
 const status=issues.length?'HOLD':empty?'NO_COUNTEREXAMPLES':'COUNTEREXAMPLES_PRESERVED';
 if(!empty&&baseline.counterexamples.length===0)issues.push('UNEXPLAINED_B180_HOLD');
 const payload={schema:SCHEMA,status:issues.length?'HOLD':status,seed,rounds,
  b180Status:baseline.status,b180Digest:baseline.attestationSha256,
  generated:generated.length,reported:baseline.counterexamples.length,processed:examples.length,
  examples,issues,caps:{maxSteps:MAX_STEPS,maxItems:MAX_ITEMS,maxInputBytes:MAX_BYTES},
  authority:{mayCreatePR:false,mayRetry:false,mayMerge:false,mayWriteDefaultBranch:false},
  governance:{witnesses:['a1','b1','c1'],observerDepth:1,noQuorum:true,isaDefined:false,
   noRepositoryCodeExecution:true,noRepositoryCIExecution:true}};
 return{...payload,attestationSha256:digest(payload)};
}
function audit(report){
 if(report?.schema!==SCHEMA||!['NO_COUNTEREXAMPLES','COUNTEREXAMPLES_PRESERVED'].includes(report.status)||
  report.issues?.length!==0||!Array.isArray(report.examples)||
  report.authority?.mayCreatePR!==false||report.authority?.mayMerge!==false||
  report.governance?.noRepositoryCodeExecution!==true)return{status:'HOLD',reason:'BOUNDARY'};
 for(const x of report.examples){
  if(x.status!=='COUNTEREXAMPLE_MINIMIZED'||x.original?.sha256!==hash(x.originalInput)||
    x.minimized?.sha256!==hash(x.minimizedInput)||x.signature!==signature(x.minimizedDecision)||
    x.signature!==signature(x.originalDecision)||x.minimizedInput.length>x.originalInput.length)
   return{status:'HOLD',reason:'COUNTEREXAMPLE_INTEGRITY'};
 }
 const {attestationSha256,...body}=report;
 return attestationSha256===digest(body)?{status:'PASS'}:{status:'HOLD',reason:'DIGEST'};
}
module.exports={SCHEMA,MAX_STEPS,observe,signature,mismatch,minimize,run,audit};
