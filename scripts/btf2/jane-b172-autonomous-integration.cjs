'use strict';
/* B172 bounded autonomous evidence-to-scratch evaluation, no remote mutations. */
const fs=require('node:fs'),path=require('node:path');
const {audit:proofAudit}=require('./jane-b168-proof-proposal.cjs');
const {inspect:inspectBase}=require('./jane-b169-drift-and-ci.cjs');
const {examine:evaluatePatch}=require('./jane-b170-isolated-evaluation.cjs');
const {bind,TTL_MS}=require('./jane-b171-triple-evidence.cjs');
const {integrate,report,stopped}=require('./jane-b172-controlled-integration.cjs');
const DIR='ecosystem/proposals',MAX=8;
function files(dir=DIR){
 if(!fs.existsSync(dir))return[];
 const xs=fs.readdirSync(dir,{withFileTypes:true})
  .filter(x=>x.isFile()&&/^[A-Za-z0-9_.-]+[.]json$/.test(x.name))
  .map(x=>path.join(dir,x.name)).sort();
 if(xs.length>MAX)throw Error('HOLD_TOO_MANY_PROPOSALS');
 return xs;
}
async function run({dir=DIR,token='',now=()=>new Date().toISOString(),inspectFn=inspectBase,
  evaluateFn=evaluatePatch,integrateFn=integrate}={}){
 const results=[];
 for(const file of files(dir)){
  let proof;
  try{proof=JSON.parse(fs.readFileSync(file,'utf8'))}
  catch{results.push(stopped('UNREADABLE_PROOF_FILE'));continue}
  if(proofAudit(proof).status!=='PASS'){results.push(stopped('INVALID_PROOF',proof));continue}
  const start=now();
  let base,local;
  try{base=await inspectFn(proof,token)}
  catch{results.push(stopped('BASE_INSPECTION_UNAVAILABLE',proof));continue}
  try{local=evaluateFn(proof)}
  catch{results.push(stopped('LOCAL_EVALUATION_UNAVAILABLE',proof));continue}
  const end=now();
  const triple=bind({proof,base,local,baseObservedAt:start,localEvaluatedAt:end,nowIso:end});
  if(triple.status!=='EVIDENCE_BOUND_NO_EXECUTION'){
   const record=stopped('B171_'+triple.reasons.join('_').slice(0,150),proof);
   record.evidenceStatus='HOLD';results.push(record);continue
  }
  const result=integrateFn({proposal:proof,base,local,triple});
  result.evidenceStatus=triple.status;result.evidenceDigest=triple.evidenceDigest;
  results.push(result);
 }
 const output=report(results);
 output.status=results.length?'OBSERVATION_COMPLETE':'HOLD_NO_PROPOSALS';
 output.noProofIsNotPass=true;
 return output;
}
async function main(){
 const args=process.argv.slice(2),i=args.indexOf('--output'),output=i<0?'ecosystem/reports/b172-latest.json':args[i+1];
 if(!output)throw Error('OUTPUT_PATH_REQUIRED');
 const r=await run({token:process.env.GITHUB_TOKEN||''});
 fs.mkdirSync(path.dirname(output),{recursive:true});
 fs.writeFileSync(output,JSON.stringify(r,null,2)+'\n');
 console.log(JSON.stringify({status:r.status,counts:r.counts,targetRepoCiExecuted:false}));
}
if(require.main===module)main().catch(e=>{console.error('HOLD '+e.message);process.exitCode=1});
module.exports={files,run};
