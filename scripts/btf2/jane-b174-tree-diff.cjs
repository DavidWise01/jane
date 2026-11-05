'use strict';
/**
 * B174 — deterministic before/after inventory proof of an exact B168 patch
 * applied to B173's bounded pinned Git-tree snapshot.
 * Target-tree files are DATA ONLY. No scripts, network writes, PRs or merges.
 */
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const {audit:proofAudit}=require('./jane-b168-proof-proposal.cjs');
const {verifyInputs}=require('./jane-b172-controlled-integration.cjs');
const {safeName,gitBlob,MAX_FILES,MAX_BYTES}=require('./jane-b173-pinned-tree.cjs');
const {TARGET,TEMPLATE}=require('./jane-b161-formic-agent.cjs');
const SCHEMA='JANE-B174-TREE-DIFF-PROOF-v1';
const sha256=b=>crypto.createHash('sha256').update(b).digest('hex');
const digest=o=>sha256(Buffer.from(JSON.stringify(o),'utf8'));
function hold(reason,proof=null){
 return{schema:SCHEMA,status:'HOLD',reason,repository:proof?.envelope?.repository||null,
  proposalSha256:proof?.sha256||null,sourceTreeSha:null,
  additions:[],modifications:[],deletions:[],preserved:0,
  temporaryWorkspaceRemoved:false,repoCodeExecuted:false,repoCiExecuted:false,
  mayCreatePR:false,mayRetry:false,mayMerge:false,mayWriteDefaultBranch:false};
}
function inventory(root,{ignoreGit=true}={}){
 const found=[],seen=new Set();let total=0;
 function walk(relative){
  const absolute=relative?path.join(root,relative):root;
  for(const dirent of fs.readdirSync(absolute,{withFileTypes:true})){
   if(ignoreGit&&relative===''&&dirent.name==='.git')continue;
   const rel=relative?relative+'/'+dirent.name:dirent.name;
   if(!safeName(rel)||seen.has(rel))throw Error('UNSAFE_OR_DUPLICATE_TREE_PATH');
   seen.add(rel);
   const full=path.join(root,rel),stat=fs.lstatSync(full);
   if(stat.isSymbolicLink()||(!stat.isDirectory()&&!stat.isFile()))throw Error('UNSUPPORTED_FILE_TYPE');
   if(stat.isDirectory()){walk(rel);continue}
   if(found.length>=MAX_FILES+1||stat.size>524288)throw Error('TREE_LIMIT');
   const bytes=fs.readFileSync(full);total+=bytes.length;
   if(total>MAX_BYTES+524288)throw Error('TREE_BYTE_LIMIT');
   found.push({path:rel,bytes:bytes.length,sha256:sha256(bytes),gitBlob:gitBlob(bytes),
    executable:!!(stat.mode&0o111)});
  }
 }
 walk('');
 return found.sort((a,b)=>a.path<b.path?-1:a.path>b.path?1:0);
}
function changes(before,after){
 const original=new Map(before.map(f=>[f.path,f])),current=new Map(after.map(f=>[f.path,f]));
 const additions=[],modifications=[],deletions=[],preserved=[];
 for(const f of after){
  const prior=original.get(f.path);
  if(!prior)additions.push(f);
  else if(prior.sha256!==f.sha256||prior.gitBlob!==f.gitBlob||prior.bytes!==f.bytes||
          prior.executable!==f.executable)modifications.push({path:f.path,before:prior,after:f});
  else preserved.push(f.path);
 }
 for(const f of before)if(!current.has(f.path))deletions.push(f.path);
 return{additions,modifications,deletions,preserved};
}
function runGit(work,args){
 const r=spawnSync('git',args,{cwd:work,encoding:'utf8',timeout:10000,maxBuffer:131072,
  env:{PATH:process.env.PATH||'',HOME:work,GIT_CONFIG_NOSYSTEM:'1',GIT_CONFIG_GLOBAL:'/dev/null'}});
 return!r.error&&r.status===0;
}
function verifyInputs174({proof,base,local,triple,scratch,tree}){
 const why=verifyInputs({proposal:proof,base,local,triple});
 if(proofAudit(proof).status!=='PASS')why.push('PROOF_INVALID');
 if(scratch?.status!=='SCRATCH_GIT_PATCH_PASS'||scratch.scratchRemoved!==true||
   scratch.proposalSha256!==proof?.sha256||scratch.baseSha!==proof?.envelope?.base?.commitSha)
  why.push('B172_SCRATCH_NOT_PASS');
 if(!tree||tree.repository!==proof?.envelope?.repository||tree.baseSha!==proof?.envelope?.base?.commitSha||
   !/^[0-9a-f]{40}$/i.test(tree.treeSha||'')||!Array.isArray(tree.blobs)||tree.blobs.length>MAX_FILES)
  why.push('B173_PINNED_SNAPSHOT_INVALID');
 if(tree?.blobs?.some(x=>!x||!x.entry||!safeName(x.entry.path)||x.entry.path===TARGET||
   !['100644','100755'].includes(x.entry.mode)||!Buffer.isBuffer(x.bytes)||
   x.bytes.length!==x.entry.size||gitBlob(x.bytes)!==x.entry.sha))
  why.push('B173_BLOB_INTEGRITY_INVALID');
 return[...new Set(why)];
}
function evaluate({proof,base,local,triple,scratch,tree},{root=os.tmpdir(),gitFn=runGit,onInventory=null}={}){
 const why=verifyInputs174({proof,base,local,triple,scratch,tree});
 if(why.length)return hold(why.join(','),proof);
 let tmp=null,removed=false,result=hold('EVALUATION_NOT_STARTED',proof);
 try{
  tmp=fs.mkdtempSync(path.join(root,'jane-b174-'));
  const work=path.join(tmp,'work');fs.mkdirSync(work);
  let total=0;
  for(const {entry,bytes} of tree.blobs){
   total+=bytes.length;if(total>MAX_BYTES)throw Error('TREE_TOO_LARGE');
   const name=path.join(work,entry.path);if(!name.startsWith(work+path.sep))throw Error('PATH_ESCAPE');
   fs.mkdirSync(path.dirname(name),{recursive:true});
   fs.writeFileSync(name,bytes,{flag:'wx',mode:entry.mode==='100755'?0o700:0o600});
  }
  const before=inventory(work);
  if(onInventory)onInventory('before',work);
  if(before.length!==tree.blobs.length||
     before.some(f=>!tree.blobs.some(x=>x.entry.path===f.path&&x.entry.sha===f.gitBlob)))
   throw Error('PRE_IMAGE_DIFFERS_FROM_SNAPSHOT');
  const patchFile=path.join(tmp,'patch.diff');
  fs.writeFileSync(patchFile,proof.envelope.proposal.changes[0].unifiedDiff,{flag:'wx',mode:0o600});
  if(!gitFn(work,['init','--quiet']))throw Error('SCRATCH_GIT_INIT_FAILED');
  if(!gitFn(work,['apply','--check','--',patchFile]))throw Error('PATCH_CHECK_FAILED');
  if(!gitFn(work,['apply','--',patchFile]))throw Error('PATCH_APPLICATION_FAILED');
  const after=inventory(work);
  if(onInventory)onInventory('after',work);
  const delta=changes(before,after),target=delta.additions[0];
  if(delta.additions.length!==1||target.path!==TARGET||delta.modifications.length||delta.deletions.length||
      delta.preserved.length!==before.length)throw Error('UNEXPECTED_TREE_DELTA');
  const expected=proof.envelope.proposal.changes[0];
  if(target.sha256!==expected.afterSha256||
      target.sha256!==sha256(Buffer.from(TEMPLATE,'utf8'))||
      target.gitBlob!==gitBlob(Buffer.from(TEMPLATE,'utf8'))||target.executable)
    throw Error('TARGET_FILE_CONTENT_OR_MODE_MISMATCH');
  const manifest={
   schema:SCHEMA,status:'EXACT_ONE_FILE_ADDITION',
   repository:proof.envelope.repository,baseSha:proof.envelope.base.commitSha,sourceTreeSha:tree.treeSha,
   proposalSha256:proof.sha256,
   before,after,delta,
   verification:{originalFilesUnchanged:true,oneAddedFile:true,sourceBlobsVerified:true,
    targetBytesMatch:true,repositoryScriptsExecuted:false,targetRepoCiExecuted:false},
   authority:{mayCreatePR:false,mayRetry:false,mayMerge:false,mayWriteDefaultBranch:false},
   mode:'READ_ONLY_PINNED_SNAPSHOT'};
  result={...manifest,manifestSha256:digest(manifest),temporaryWorkspaceRemoved:false};
 }catch(e){result=hold(String(e.message||e).slice(0,160),proof)}
 finally{
  if(tmp!==null){try{fs.rmSync(tmp,{recursive:true,force:true});removed=true}
   catch{result=hold('TEMP_WORKSPACE_CLEANUP_FAILED',proof)}}
 }
 result.temporaryWorkspaceRemoved=removed;
 if(!removed)result.status='HOLD';
 return result;
}
function audit(record){
 if(record?.schema!==SCHEMA||record.status!=='EXACT_ONE_FILE_ADDITION'||
   record.temporaryWorkspaceRemoved!==true||!Array.isArray(record.before)||!Array.isArray(record.after))
  return{status:'HOLD',reason:'SCHEMA_OR_CLEANUP'};
 const {manifestSha256,temporaryWorkspaceRemoved,...body}=record;
 if(digest(body)!==manifestSha256)return{status:'HOLD',reason:'DIGEST'};
 const delta=changes(record.before,record.after);
 if(delta.additions.length!==1||delta.additions[0].path!==TARGET||
    delta.modifications.length||delta.deletions.length||delta.preserved.length!==record.before.length||
    record.authority?.mayCreatePR!==false||record.authority?.mayMerge!==false||
    record.verification?.targetRepoCiExecuted!==false)return{status:'HOLD',reason:'DELTA_OR_AUTHORITY'};
 return{status:'PASS',manifestSha256};
}
module.exports={SCHEMA,inventory,changes,verifyInputs174,evaluate,audit,hold};
