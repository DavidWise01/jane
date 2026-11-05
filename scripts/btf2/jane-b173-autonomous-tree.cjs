'use strict';
/** B173: bounded autonomous data-only pinned tree evaluation for committed proofs. */
const fs=require('node:fs'),path=require('node:path');
const {audit:proofAudit}=require('./jane-b168-proof-proposal.cjs');
const {inspect:inspectBase}=require('./jane-b169-drift-and-ci.cjs');
const {examine:evalLocal}=require('./jane-b170-isolated-evaluation.cjs');
const {bind}=require('./jane-b171-triple-evidence.cjs');
const {integrate:evalScratch}=require('./jane-b172-controlled-integration.cjs');
const {readPinned,applySnapshot,hold}=require('./jane-b173-pinned-tree.cjs');
const MAX=8,DIR='ecosystem/proposals';
function candidates(dir=DIR){
 if(!fs.existsSync(dir))return[];
 const names=fs.readdirSync(dir,{withFileTypes:true}).filter(x=>x.isFile()&&/^[A-Za-z0-9_.-]+[.]json$/.test(x.name))
  .map(x=>path.join(dir,x.name)).sort();
 if(names.length>MAX)throw Error('TOO_MANY_PROPOSALS');
 return names;
}
async function run({dir=DIR,token='',clock=()=>new Date().toISOString(),inspect=inspectBase,
 localEval=evalLocal,scratchEval=evalScratch,snapshotFn=readPinned,applyFn=applySnapshot}={}){
 const records=[];
 for(const filename of candidates(dir)){
  let proof;
  try{proof=JSON.parse(fs.readFileSync(filename,'utf8'))}catch{records.push(hold('UNREADABLE_PROOF'));continue}
  if(proofAudit(proof).status!=='PASS'){records.push(hold('INVALID_B168_PROOF',proof));continue}
  const start=clock();
  let base,local,scratch,tree;
  try{base=await inspect(proof,token);local=localEval(proof)}
  catch{records.push(hold('B169_OR_B170_UNAVAILABLE',proof));continue}
  const afterLocal=clock(),triple=bind({proof,base,local,baseObservedAt:start,localEvaluatedAt:afterLocal,nowIso:afterLocal});
  if(triple.status!=='EVIDENCE_BOUND_NO_EXECUTION'){records.push(hold('B171_'+triple.reasons.join(',').slice(0,120),proof));continue}
  try{scratch=scratchEval({proposal:proof,base,local,triple})}
  catch{records.push(hold('B172_SCRATCH_UNAVAILABLE',proof));continue}
  if(scratch.status!=='SCRATCH_GIT_PATCH_PASS'||scratch.scratchRemoved!==true){
   records.push(hold('B172_SCRATCH_HOLD',proof));continue
  }
  try{tree=await snapshotFn(proof,token)}
  catch(e){records.push(hold('PINNED_TREE_'+String(e.message).slice(0,100),proof));continue}
  if(Date.parse(clock())-Date.parse(start)>300000){
   records.push(hold('B171_EVIDENCE_EXPIRED',proof));continue
  }
  let result;
  try{result=applyFn({proof,base,local,triple,scratch,tree})}
  catch{result=hold('TREE_PATCH_EVALUATION_ERROR',proof)}
  result.evidenceDigest=triple.evidenceDigest;
  records.push(result);
 }
 return{schema:'JANE-B173-PINNED-TREE-REPORT-v1',mode:'READ_ONLY_SNAPSHOT',
   status:records.length?'OBSERVATIONS_RECORDED':'HOLD_NO_PROPOSALS',
   results:records,
   counts:{observed:records.length,passed:records.filter(x=>x.status==='PINNED_TREE_PATCH_PASS').length,
    held:records.filter(x=>x.status==='HOLD').length},
   governance:{witnesses:['a1','b1','c1'],observerDepth:1,noQuorum:true,isaDefined:false,
    noRepositoryCodeExecuted:true,actualRepositoryCIExecuted:false,automaticWrites:false,automaticMerge:false}};
}
async function main(){
 const args=process.argv.slice(2),i=args.indexOf('--output'),dest=i<0?'ecosystem/reports/b173-latest.json':args[i+1];
 if(!dest)throw Error('OUTPUT_REQUIRED');
 const record=await run({token:process.env.GITHUB_TOKEN||''});
 fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(record,null,2)+'\n');
 console.log(JSON.stringify({status:record.status,counts:record.counts,repoCodeExecuted:false}));
}
if(require.main===module)main().catch(e=>{console.error('HOLD '+e.message);process.exitCode=1});
module.exports={candidates,run};
