'use strict';
/**
 * B173: bounded data-only snapshot of a pinned target Git tree.
 * No clone, no remote code execution, no repository writes, no PR creation.
 */
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const {audit:proofAudit}=require('./jane-b168-proof-proposal.cjs');
const {verifyInputs}=require('./jane-b172-controlled-integration.cjs');
const {TARGET,TEMPLATE}=require('./jane-b161-formic-agent.cjs');
const MAX_FILES=200,MAX_BYTES=2*1024*1024,MAX_ONE=512*1024,OWNER='DavidWise01';
const sha40=x=>typeof x==='string'&&/^[0-9a-f]{40}$/i.test(x);
const gitBlob=bytes=>crypto.createHash('sha1').update(Buffer.from('blob '+bytes.length+'\0')).update(bytes).digest('hex');
function safeName(name){
 if(typeof name!=='string'||!name||name.length>400||name.includes('\\')||name.includes('\0')||
    name.startsWith('/')||name.includes('//'))return false;
 return name.split('/').every(part=>part.length>0&&part!=='.'&&part!=='..'&&part!=='.git');
}
function planTree(tree,target=TARGET){
 if(!tree||tree.truncated!==false||!Array.isArray(tree.tree))return{status:'HOLD',reason:'TREE_TRUNCATED_OR_UNAVAILABLE'};
 if(tree.tree.length>MAX_FILES)return{status:'HOLD',reason:'TREE_FILE_LIMIT'};
 const seen=new Set(),files=[];let total=0;
 for(const e of tree.tree){
  if(!safeName(e.path)||seen.has(e.path))return{status:'HOLD',reason:'UNSAFE_OR_DUPLICATE_PATH'};
  seen.add(e.path);
  if(e.type==='tree')continue;
  if(e.type!=='blob'||!['100644','100755'].includes(e.mode)||!sha40(e.sha)||
      !Number.isInteger(e.size)||e.size<0||e.size>MAX_ONE)return{status:'HOLD',reason:'UNSUPPORTED_BLOB_OR_MODE'};
  total+=e.size;if(total>MAX_BYTES)return{status:'HOLD',reason:'TREE_BYTE_LIMIT'};
  files.push({path:e.path,sha:e.sha,size:e.size,mode:e.mode});
 }
 if(seen.has(target))return{status:'HOLD',reason:'TARGET_ALREADY_EXISTS'};
 const paths=new Set(files.map(f=>f.path));
 if([...paths].some(p=>target.startsWith(p+'/')))return{status:'HOLD',reason:'TARGET_PARENT_IS_FILE'};
 return{status:'SNAPSHOT_PLAN',files,totalBytes:total};
}
function decodeBlob(blob,entry){
 if(!blob||blob.encoding!=='base64'||typeof blob.content!=='string')throw Error('BLOB_ENCODING');
 const raw=blob.content.replace(/\s/g,'');
 const bytes=Buffer.from(raw,'base64');
 if(bytes.toString('base64')!==raw||bytes.length!==entry.size||gitBlob(bytes)!==entry.sha||
    blob.sha!==entry.sha||blob.size!==entry.size)throw Error('BLOB_MISMATCH');
 return bytes;
}
const encode=encodeURIComponent;
async function api(route,token){
 const headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'jane-b173-tree-snapshot'};
 if(token)headers.Authorization='Bearer '+token;
 const response=await fetch('https://api.github.com'+route,{method:'GET',headers});
 if(!response.ok)throw Error('GITHUB_HTTP_'+response.status);
 return response.json();
}
async function readPinned(proof,token='',fetchFn=api){
 if(proofAudit(proof).status!=='PASS')throw Error('INVALID_PROOF');
 const e=proof.envelope,repo=e.repository,base=e.base;
 if(!/^DavidWise01\/[A-Za-z0-9._-]+$/.test(repo)||!sha40(base.commitSha))throw Error('SCOPE_OR_SHA');
 const root='/repos/'+repo,metadata=await fetchFn(root,token);
 if(metadata?.full_name!==repo||metadata?.owner?.login!==OWNER||metadata?.private!==false||
   metadata?.archived===true||metadata?.fork===true||metadata?.disabled===true||
   metadata?.default_branch!==base.branch)throw Error('REPO_SCOPE_CHANGED');
 const refPath=root+'/git/ref/heads/'+encode(base.branch);
 const start=await fetchFn(refPath,token);
 if(start?.object?.sha!==base.commitSha)throw Error('BASE_SHA_DRIFT');
 const commit=await fetchFn(root+'/git/commits/'+encode(base.commitSha),token);
 if(commit?.sha!==base.commitSha||!sha40(commit.tree?.sha))throw Error('UNPINNED_TREE');
 const tree=await fetchFn(root+'/git/trees/'+encode(commit.tree.sha)+'?recursive=1',token);
 const plan=planTree(tree);
 if(plan.status!=='SNAPSHOT_PLAN')throw Error(plan.reason);
 const blobs=[];let read=0;
 for(const file of plan.files){
  const item=await fetchFn(root+'/git/blobs/'+encode(file.sha),token);
  const bytes=decodeBlob(item,file);read+=bytes.length;
  if(read>MAX_BYTES)throw Error('BYTE_CAP');
  blobs.push({entry:file,bytes});
 }
 const end=await fetchFn(refPath,token);
 if(end?.object?.sha!==base.commitSha)throw Error('BASE_MOVED_DURING_SNAPSHOT');
 return{repository:repo,baseSha:base.commitSha,treeSha:commit.tree.sha,blobs,
  files:blobs.length,totalBytes:read,source:'GITHUB_PINNED_GIT_TREE'};
}
function git(cwd,args){
 const r=spawnSync('git',args,{cwd,encoding:'utf8',timeout:10000,maxBuffer:131072,
  env:{PATH:process.env.PATH||'',HOME:cwd,GIT_CONFIG_NOSYSTEM:'1',GIT_CONFIG_GLOBAL:'/dev/null'}});
 return !r.error&&r.status===0;
}
function hold(reason,proposal){
 return{schema:'JANE-B173-PINNED-TREE-INTEGRATION-v1',status:'HOLD',reason,
  repository:proposal?.envelope?.repository||null,proposalSha256:proposal?.sha256||null,
  targetRepoCiExecuted:false,targetRepoCodeExecuted:false,mayWriteRepo:false,mayCreatePR:false,
  mayMerge:false,cleanupConfirmed:false};
}
function applySnapshot({proof,base,local,triple,scratch,tree},opts={}){
 const reasons=verifyInputs({proposal:proof,base,local,triple});
 if(reasons.length)return hold('B172_'+reasons.join(','),proof);
 if(!scratch||scratch.baseSha!==proof.envelope.base.commitSha||scratch.status!=='SCRATCH_GIT_PATCH_PASS'||
   scratch.proposalSha256!==proof.sha256||scratch.scratchRemoved!==true)return hold('B172_SCRATCH_UNVERIFIED',proof);
 if(!tree||tree.baseSha!==proof.envelope.base.commitSha||tree.repository!==proof.envelope.repository||
   !Array.isArray(tree.blobs)||tree.blobs.length>MAX_FILES)return hold('PINNED_TREE_MISSING',proof);
 const root=opts.root||os.tmpdir();let tmp=null,cleaned=false,result=hold('EVALUATION_NOT_COMPLETED',proof);
 try{
  tmp=fs.mkdtempSync(path.join(root,'jane-b173-'));
  let total=0;const seen=new Set();
  for(const {entry,bytes} of tree.blobs){
   if(!safeName(entry.path)||entry.path===TARGET||seen.has(entry.path)||
      !Buffer.isBuffer(bytes)||bytes.length!==entry.size||gitBlob(bytes)!==entry.sha)throw Error('TREE_BLOB_INVALID');
   total+=bytes.length;if(total>MAX_BYTES)throw Error('TREE_TOO_LARGE');
   seen.add(entry.path);
   const dst=path.resolve(tmp,entry.path);
   if(!dst.startsWith(tmp+path.sep))throw Error('ESCAPE');
   fs.mkdirSync(path.dirname(dst),{recursive:true});
   fs.writeFileSync(dst,bytes,{flag:'wx',mode:0o600});
  }
  const patch=path.join(tmp,'patch.diff');
  // The patch must not appear in the source snapshot and cannot overwrite source.
  if(seen.has('patch.diff'))throw Error('PATCH_PATH_COLLISION');
  fs.writeFileSync(patch,proof.envelope.proposal.changes[0].unifiedDiff,{flag:'wx',mode:0o600});
  if(!git(tmp,['init','--quiet'])||!git(tmp,['apply','--check','--',patch])||
     !git(tmp,['apply','--',patch]))throw Error('GIT_APPLY_FAILED');
  const target=path.resolve(tmp,TARGET),bytes=fs.readFileSync(target);
  if(bytes.toString('utf8')!==TEMPLATE||
     crypto.createHash('sha256').update(bytes).digest('hex')!==proof.envelope.proposal.changes[0].afterSha256)
     throw Error('PATCH_OUTPUT_MISMATCH');
  for(const {entry,bytes:original} of tree.blobs){
   if(!fs.readFileSync(path.join(tmp,entry.path)).equals(original))throw Error('SOURCE_TREE_MUTATED');
  }
  result={schema:'JANE-B173-PINNED-TREE-INTEGRATION-v1',status:'PINNED_TREE_PATCH_PASS',
   repository:proof.envelope.repository,proposalSha256:proof.sha256,baseSha:tree.baseSha,
   treeSha:tree.treeSha,sourceFilesChecked:tree.blobs.length,sourceBytesChecked:total,
   checks:['PINNED_GIT_TREE','ALL_BLOB_HASHES','PATCH_APPLY_CHECK','PATCH_APPLY','EXACT_TARGET_BYTES','SOURCE_UNCHANGED'],
   targetRepoCiExecuted:false,targetRepoCodeExecuted:false,mayWriteRepo:false,
   mayCreatePR:false,mayMerge:false,cleanupConfirmed:false};
 }catch(e){result=hold(String(e.message).slice(0,90),proof)}
 finally{if(tmp){try{fs.rmSync(tmp,{recursive:true,force:true});cleaned=true}catch{result=hold('CLEANUP_FAILED',proof)}}}
 result.cleanupConfirmed=cleaned;
 if(!cleaned)result.status='HOLD';
 return result;
}
module.exports={MAX_FILES,MAX_BYTES,safeName,planTree,decodeBlob,readPinned,applySnapshot,hold,gitBlob};
