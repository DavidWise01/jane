'use strict';
/** B175 autonomous reproducibility read-only scanner, at most 8 real proof files. */
const fs=require('node:fs'),path=require('node:path');
const {audit:proofAudit}=require('./jane-b168-proof-proposal.cjs');
const {inspect:observeBase}=require('./jane-b169-drift-and-ci.cjs');
const {examine:localCheck}=require('./jane-b170-isolated-evaluation.cjs');
const {bind}=require('./jane-b171-triple-evidence.cjs');
const {integrate:scratchCheck}=require('./jane-b172-controlled-integration.cjs');
const {readPinned}=require('./jane-b173-pinned-tree.cjs');
const {evaluate:treeManifest}=require('./jane-b174-tree-diff.cjs');
const {evaluate:repeat,registry,reject,audit}=require('./jane-b175-reproducibility.cjs');
const DIR='ecosystem/proposals',MAX=8;
function files(dir=DIR){
 if(!fs.existsSync(dir))return[];
 const entries=fs.readdirSync(dir,{withFileTypes:true}).filter(x=>x.isFile()&&/^[A-Za-z0-9_.-]+[.]json$/.test(x.name))
  .map(x=>path.join(dir,x.name)).sort();
 if(entries.length>MAX)throw Error('TOO_MANY_PROPOSALS');
 return entries;
}
async function scan({dir=DIR,token='',now=()=>new Date().toISOString(),
 observe=observeBase,local=localCheck,scratch=scratchCheck,snapshot=readPinned,
 repeatFn=treeManifest}={}){
 const results=[];
 for(const file of files(dir)){
  let proof;
  try{proof=JSON.parse(fs.readFileSync(file,'utf8'))}
  catch{results.push(reject('PROOF_READ_FAILED'));continue}
  if(proofAudit(proof).status!=='PASS'){results.push(reject('INVALID_B168_PROOF',proof));continue}
  const started=now();
  let base,localEvidence,scratchEvidence,tree;
  try{base=await observe(proof,token);localEvidence=local(proof)}
  catch{results.push(reject('BASE_OR_LOCAL_UNAVAILABLE',proof));continue}
  const checked=now();
  const triple=bind({proof,base,local:localEvidence,baseObservedAt:started,localEvaluatedAt:checked,nowIso:checked});
  if(triple.status!=='EVIDENCE_BOUND_NO_EXECUTION'){
   results.push(reject('B171_'+triple.reasons.join(',').slice(0,100),proof));continue
  }
  try{scratchEvidence=scratch({proposal:proof,base,local:localEvidence,triple})}
  catch{results.push(reject('B172_SCRATCH_EXCEPTION',proof));continue}
  if(scratchEvidence.status!=='SCRATCH_GIT_PATCH_PASS'||scratchEvidence.scratchRemoved!==true){
   results.push(reject('B172_SCRATCH_HOLD',proof));continue
  }
  try{tree=await snapshot(proof,token)}
  catch(e){results.push(reject('B173_'+String(e.message||e).slice(0,100),proof));continue}
  const age=Date.parse(now())-Date.parse(started);
  if(!Number.isFinite(age)||age<0||age>300000){
   results.push(reject('STALE_BOUND_EVIDENCE',proof));continue
  }
  let result;
  try{result=repeat({proof,base,local:localEvidence,triple,scratch:scratchEvidence,tree},{repeatFn})}
  catch{result=reject('B175_REPEAT_EXCEPTION',proof)}
  if(result.status==='REPRODUCIBLE_TREE_DELTA_NO_EXECUTION'&&audit(result).status!=='PASS')
   result=reject('B175_ATTESTATION_AUDIT_FAILED',proof);
  results.push(result);
 }
 return registry(results);
}
async function main(){
 const args=process.argv.slice(2),idx=args.indexOf('--output');
 const dest=idx>=0?args[idx+1]:'ecosystem/reports/b175-latest.json';
 if(!dest)throw Error('OUTPUT_REQUIRED');
 const r=await scan({token:process.env.GITHUB_TOKEN||''});
 fs.mkdirSync(path.dirname(dest),{recursive:true});
 fs.writeFileSync(dest,JSON.stringify(r,null,2)+'\n');
 console.log(JSON.stringify({status:r.status,counts:r.counts,mayWrite:false}));
}
if(require.main===module)main().catch(e=>{console.error('HOLD '+e.message);process.exitCode=1});
module.exports={files,scan};
