'use strict';
/** B176 read-only differential audit of committed proofs, no target code execution. */
const fs=require('node:fs'),path=require('node:path');
const {audit:proofAudit}=require('./jane-b168-proof-proposal.cjs');
const {inspect:observeBase}=require('./jane-b169-drift-and-ci.cjs');
const {examine:localCheck}=require('./jane-b170-isolated-evaluation.cjs');
const {bind}=require('./jane-b171-triple-evidence.cjs');
const {integrate:scratchCheck}=require('./jane-b172-controlled-integration.cjs');
const {readPinned}=require('./jane-b173-pinned-tree.cjs');
const {evaluate:diff,audit,registry,hold}=require('./jane-b176-differential-tree.cjs');
const MAX=8;
function files(dir='ecosystem/proposals'){
 if(!fs.existsSync(dir))return[];
 const items=fs.readdirSync(dir,{withFileTypes:true})
  .filter(x=>x.isFile()&&/^[A-Za-z0-9_.-]+[.]json$/.test(x.name))
  .map(x=>path.join(dir,x.name)).sort();
 if(items.length>MAX)throw Error('TOO_MANY_PROPOSALS');
 return items;
}
async function scan({dir='ecosystem/proposals',token='',clock=()=>new Date().toISOString(),
 observe=observeBase,local=localCheck,scratch=scratchCheck,pinned=readPinned,compare=diff}={}){
 const results=[];
 for(const file of files(dir)){
  let proof;
  try{proof=JSON.parse(fs.readFileSync(file,'utf8'))}
  catch{results.push(hold('PROOF_READ_FAILED'));continue}
  if(proofAudit(proof).status!=='PASS'){results.push(hold('INVALID_B168_PROOF',proof));continue}
  const start=clock();
  let base,localEvidence,scratchEvidence,tree;
  try{base=await observe(proof,token);localEvidence=local(proof)}
  catch{results.push(hold('BASE_OR_LOCAL_UNAVAILABLE',proof));continue}
  const localDone=clock();
  const triple=bind({proof,base,local:localEvidence,baseObservedAt:start,localEvaluatedAt:localDone,nowIso:localDone});
  if(triple.status!=='EVIDENCE_BOUND_NO_EXECUTION'){
   results.push(hold('B171_'+triple.reasons.join(',').slice(0,120),proof));continue
  }
  try{scratchEvidence=scratch({proposal:proof,base,local:localEvidence,triple})}
  catch{results.push(hold('B172_UNAVAILABLE',proof));continue}
  if(scratchEvidence.status!=='SCRATCH_GIT_PATCH_PASS'||scratchEvidence.scratchRemoved!==true){
   results.push(hold('B172_SCRATCH_HOLD',proof));continue
  }
  try{tree=await pinned(proof,token)}
  catch(e){results.push(hold('B173_'+String(e.message||e).slice(0,110),proof));continue}
  const nowMs=Date.parse(clock()),startMs=Date.parse(start);
  if(!Number.isFinite(nowMs)||!Number.isFinite(startMs)||nowMs<startMs||nowMs-startMs>300000){
   results.push(hold('EVIDENCE_EXPIRED',proof));continue
  }
  let record;
  try{record=compare({proof,base,local:localEvidence,triple,scratch:scratchEvidence,tree})}
  catch{record=hold('DIFFERENTIAL_EVALUATION_EXCEPTION',proof)}
  if(record.status==='DIFFERENTIAL_TREE_AGREEMENT_NO_EXECUTION'&&audit(record).status!=='PASS')
   record=hold('ATTESTATION_AUDIT_FAILED',proof);
  results.push(record);
 }
 return registry(results);
}
async function main(){
 const argv=process.argv.slice(2),at=argv.indexOf('--output');
 const dest=at>=0?argv[at+1]:'ecosystem/reports/b176-latest.json';
 if(!dest)throw Error('OUTPUT_PATH_REQUIRED');
 const report=await scan({token:process.env.GITHUB_TOKEN||''});
 fs.mkdirSync(path.dirname(dest),{recursive:true});
 fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({status:report.status,counts:report.counts,noWrites:true}));
}
if(require.main===module)main().catch(e=>{console.error('HOLD '+e.message);process.exitCode=1});
module.exports={files,scan};
