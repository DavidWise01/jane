'use strict';
/**
 * B176 independently walks the same on-disk tree used by B174.
 * No B174 inventory(), changes(), or gitBlob() functions are reused here.
 * No repository source code is executed and no GitHub writes are made.
 */
const fs=require('node:fs'),crypto=require('node:crypto'),path=require('node:path');
const {evaluate:evaluate174,audit:audit174}=require('./jane-b174-tree-diff.cjs');
const TARGET='.github/ISSUE_TEMPLATE/bug_report.md';
const SCHEMA='JANE-B176-DIFFERENTIAL-TREE-AUDIT-v1';
const sha256=b=>crypto.createHash('sha256').update(b).digest('hex');
const digest=o=>sha256(Buffer.from(JSON.stringify(o),'utf8'));
function independentInventory(root){
 const pending=[{absolute:root,relative:''}],files=[],seen=new Set();
 let bytesTotal=0,scanned=0;
 while(pending.length){
  const {absolute,relative}=pending.pop();
  const names=fs.readdirSync(absolute).sort().reverse();
  for(const name of names){
   if(!relative&&name==='.git')continue;
   const rel=relative?relative+'/'+name:name;
   if(!name||name==='.'||name==='..'||name.includes('\\')||name.includes('\0')||
      !rel||rel.startsWith('/')||rel.length>400||rel.split('/').includes('.git')||
      rel.split('/').includes('..')||seen.has(rel))throw Error('INDEPENDENT_UNSAFE_PATH');
   seen.add(rel);
   const file=path.join(absolute,name),stat=fs.lstatSync(file);
   if(stat.isSymbolicLink())throw Error('INDEPENDENT_SYMLINK');
   if(stat.isDirectory()){pending.push({absolute:file,relative:rel});continue}
   if(!stat.isFile()||++scanned>201||stat.size>524288)throw Error('INDEPENDENT_FILE_LIMIT');
   const buffer=fs.readFileSync(file);
   bytesTotal+=buffer.length;
   if(bytesTotal>2621440)throw Error('INDEPENDENT_BYTE_LIMIT');
   const blobHeader=Buffer.from('blob '+buffer.length+'\0','utf8');
   files.push({
    path:rel,bytes:buffer.length,
    sha256:sha256(buffer),
    gitBlob:crypto.createHash('sha1').update(blobHeader).update(buffer).digest('hex'),
    executable:(stat.mode&0o111)!==0
   });
  }
 }
 files.sort((a,b)=>a.path<b.path?-1:a.path>b.path?1:0);
 return files;
}
function hold(reason,proof){
 return{schema:SCHEMA,status:'HOLD',reasons:[reason],repository:proof?.envelope?.repository??null,
  proposalSha256:proof?.sha256??null,independentBefore:null,independentAfter:null,
  automaticWrites:false,mayCreatePR:false,mayRetry:false,mayMerge:false,
  targetRepositoryCodeExecuted:false};
}
function evaluate(input,{evaluateFn=evaluate174,independentFn=independentInventory}={}){
 const observed={};
 let b174;
 try{
  b174=evaluateFn(input,{onInventory:(stage,root)=>{
   if(stage!=='before'&&stage!=='after'||observed[stage])throw Error('INVALID_OBSERVATION_STAGE');
   observed[stage]=independentFn(root);
  }});
 }catch(e){return hold('B174_OR_OBSERVER_EXCEPTION',input?.proof)}
 if(b174?.status!=='EXACT_ONE_FILE_ADDITION'||audit174(b174).status!=='PASS'||
    b174.temporaryWorkspaceRemoved!==true)return hold('B174_AUDIT_HOLD',input?.proof);
 if(!observed.before||!observed.after)return hold('MISSING_INDEPENDENT_SNAPSHOT',input?.proof);
 const same=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
 if(!same(observed.before,b174.before))return hold('BEFORE_INVENTORY_DISAGREEMENT',input?.proof);
 if(!same(observed.after,b174.after))return hold('AFTER_INVENTORY_DISAGREEMENT',input?.proof);
 const old=new Map(observed.before.map(f=>[f.path,f]));
 const current=new Map(observed.after.map(f=>[f.path,f]));
 if(old.size!==observed.before.length||current.size!==observed.after.length)
  return hold('DUPLICATE_PATHS',input?.proof);
 const added=observed.after.filter(f=>!old.has(f.path));
 const changed=observed.after.filter(f=>old.has(f.path)&&!same(old.get(f.path),f));
 const removed=observed.before.filter(f=>!current.has(f.path));
 if(added.length!==1||added[0].path!==TARGET||changed.length!==0||removed.length!==0)
  return hold('INDEPENDENT_CHANGESET_DISAGREEMENT',input?.proof);
 const e={schema:SCHEMA,status:'DIFFERENTIAL_TREE_AGREEMENT_NO_EXECUTION',
  reasons:[],repository:b174.repository,proposalSha256:b174.proposalSha256,baseSha:b174.baseSha,
  sourceTreeSha:b174.sourceTreeSha,b174ManifestSha256:b174.manifestSha256,
  independentBeforeSha256:digest(observed.before),independentAfterSha256:digest(observed.after),
  independentAddedPaths:added.map(x=>x.path),independentPreservedCount:observed.before.length,
  identicalBefore:true,identicalAfter:true,independentAlgorithm:true,
  targetRepositoryCodeExecuted:false,targetRepositoryCiExecuted:false,
  mayCreatePR:false,mayRetry:false,mayMerge:false,mayWriteDefaultBranch:false};
 return{...e,attestationSha256:digest(e)};
}
function audit(record){
 if(record?.schema!==SCHEMA||record.status!=='DIFFERENTIAL_TREE_AGREEMENT_NO_EXECUTION'||
  record.identicalBefore!==true||record.identicalAfter!==true||record.independentAlgorithm!==true||
  record.targetRepositoryCodeExecuted!==false||record.targetRepositoryCiExecuted!==false||
  record.mayCreatePR!==false||record.mayMerge!==false||record.mayRetry!==false||
  record.mayWriteDefaultBranch!==false||JSON.stringify(record.independentAddedPaths)!==JSON.stringify([TARGET]))
   return{status:'HOLD',reason:'BOUNDARY'};
 const {attestationSha256,...body}=record;
 return attestationSha256===digest(body)?{status:'PASS',digest:attestationSha256}:{status:'HOLD',reason:'DIGEST'};
}
function registry(results){
 if(!Array.isArray(results)||results.length>8)throw Error('B176_RECORD_LIMIT');
 return{schema:'JANE-B176-DIFFERENTIAL-REGISTRY-v1',mode:'READ_ONLY',
  status:results.length?'OBSERVATIONS_RECORDED':'HOLD_NO_PROPOSALS',
  results,counts:{observed:results.length,agreed:results.filter(x=>x.status==='DIFFERENTIAL_TREE_AGREEMENT_NO_EXECUTION').length,
   held:results.filter(x=>x.status==='HOLD').length},
  governance:{witnesses:['a1','b1','c1'],observerDepth:1,noQuorum:true,isaDefined:false,
   automaticWrites:false,automaticMerges:false,targetRepositoryCodeExecuted:false}};
}
module.exports={SCHEMA,independentInventory,evaluate,audit,registry,hold};
