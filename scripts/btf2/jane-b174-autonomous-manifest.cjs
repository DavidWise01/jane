'use strict';
/* B174 read-only autonomous evidence chain and on-disk tree-diff verification. */
const fs=require('node:fs'),path=require('node:path');
const {audit:proofAudit}=require('./jane-b168-proof-proposal.cjs');
const {inspect:observeBase}=require('./jane-b169-drift-and-ci.cjs');
const {examine:checkLocal}=require('./jane-b170-isolated-evaluation.cjs');
const {bind}=require('./jane-b171-triple-evidence.cjs');
const {integrate:checkScratch}=require('./jane-b172-controlled-integration.cjs');
const {readPinned}=require('./jane-b173-pinned-tree.cjs');
const {evaluate,hold,audit}=require('./jane-b174-tree-diff.cjs');
const DIR='ecosystem/proposals',MAX=8;
function candidates(dir=DIR){
 if(!fs.existsSync(dir))return[];
 const names=fs.readdirSync(dir,{withFileTypes:true})
  .filter(x=>x.isFile()&&/^[A-Za-z0-9_.-]+[.]json$/.test(x.name))
  .map(x=>path.join(dir,x.name)).sort();
 if(names.length>MAX)throw Error('TOO_MANY_PROPOSALS');
 return names;
}
async function run({dir=DIR,token='',now=()=>new Date().toISOString(),observe=observeBase,
  check=checkLocal,scratch=checkScratch,pinned=readPinned,treeDiff=evaluate}={}){
 const entries=[];
 for(const f of candidates(dir)){
  let proof;try{proof=JSON.parse(fs.readFileSync(f,'utf8'))}
  catch{entries.push(hold('UNREADABLE_PROOF_FILE'));continue}
  if(proofAudit(proof).status!=='PASS'){entries.push(hold('INVALID_B168_PROOF',proof));continue}
  const started=now();
  let base,local,scratchResult,tree;
  try{base=await observe(proof,token);local=check(proof)}
  catch{entries.push(hold('B169_OR_B170_UNAVAILABLE',proof));continue}
  const finished=now();
  const triple=bind({proof,base,local,baseObservedAt:started,localEvaluatedAt:finished,nowIso:finished});
  if(triple.status!=='EVIDENCE_BOUND_NO_EXECUTION'){
   entries.push(hold('B171_'+triple.reasons.join(',').slice(0,140),proof));continue
  }
  try{scratchResult=scratch({proposal:proof,base,local,triple})}
  catch{entries.push(hold('B172_UNAVAILABLE',proof));continue}
  if(scratchResult.status!=='SCRATCH_GIT_PATCH_PASS'||scratchResult.scratchRemoved!==true){
   entries.push(hold('B172_SCRATCH_HOLD',proof));continue
  }
  try{tree=await pinned(proof,token)}
  catch(e){entries.push(hold('B173_'+String(e.message||e).slice(0,130),proof));continue}
  const t=Date.parse(now())-Date.parse(started);
  if(!Number.isFinite(t)||t<0||t>300000){
   entries.push(hold('TRIPLE_EVIDENCE_STALE',proof));continue
  }
  let manifest;
  try{manifest=treeDiff({proof,base,local,triple,scratch:scratchResult,tree})}
  catch{manifest=hold('B174_EVALUATION_ERROR',proof)}
  if(manifest.status==='EXACT_ONE_FILE_ADDITION'&&audit(manifest).status!=='PASS')
   manifest=hold('B174_MANIFEST_AUDIT_HOLD',proof);
  entries.push(manifest);
 }
 return{schema:'JANE-B174-MANIFEST-REPORT-v1',mode:'READ_ONLY_PINNED_TREE_DIFF',
  status:entries.length?'OBSERVATIONS_RECORDED':'HOLD_NO_PROPOSALS',
  entries,counts:{observed:entries.length,exactDelta:entries.filter(x=>x.status==='EXACT_ONE_FILE_ADDITION').length,
    held:entries.filter(x=>x.status==='HOLD').length},
  governance:{witnesses:['a1','b1','c1'],observerDepth:1,noQuorum:true,isaDefined:false,
    repositoryCodeExecuted:false,repositoryCiExecuted:false,automaticWrites:false,automaticMerges:false}};
}
async function main(){
 const args=process.argv.slice(2),at=args.indexOf('--output'),dest=at<0?'ecosystem/reports/b174-latest.json':args[at+1];
 if(!dest)throw Error('OUTPUT_REQUIRED');
 const result=await run({token:process.env.GITHUB_TOKEN||''});
 fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({status:result.status,counts:result.counts,noWrites:true}));
}
if(require.main===module)main().catch(e=>{console.error('HOLD '+e.message);process.exitCode=1});
module.exports={candidates,run};
