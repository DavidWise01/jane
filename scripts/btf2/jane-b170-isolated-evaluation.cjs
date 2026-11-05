'use strict';
/** B170: isolated evaluation of one fixed B168 patch. No remote code execution. */
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),crypto=require('node:crypto');
const {audit}=require('./jane-b168-proof-proposal.cjs');
const {TARGET,TEMPLATE}=require('./jane-b161-formic-agent.cjs');
const MODE='FIXED_TEMPLATE_LOCAL_VALIDATION';
const digest=s=>crypto.createHash('sha256').update(Buffer.from(s,'utf8')).digest('hex');
function hold(reason,repo=null){return{schema:'JANE-B170-ISOLATED-REPAIR-EVALUATION-v1',status:'HOLD',reason,repository:repo,
  mode:MODE,checks:[],workspaceDeleted:true,proposalTestsExecuted:false,
  mayCreatePR:false,mayMerge:false,mayRetry:false,defaultBranchWrites:false}}
function examine(proof,{tempRoot=os.tmpdir(),existingTarget=false,makeTemp=fs.mkdtempSync,
  write=fs.writeFileSync,read=fs.readFileSync,remove=fs.rmSync}={}){
 const repo=proof?.envelope?.repository||null;
 if(audit(proof).status!=='PASS')return hold('INVALID_B168_PROOF',repo);
 const e=proof.envelope,change=e.proposal.changes[0];
 if(change.operation!=='ADD_FILE'||change.path!==TARGET||change.after!==TEMPLATE||existingTarget)
   return hold('UNSAFE_OR_ALREADY_PRESENT_TARGET',repo);
 let temp=null,result;
 const checks=[],record=(name,ok,detail)=>checks.push({name,status:ok?'PASS':'FAIL',detail});
 try{
  temp=makeTemp(path.join(tempRoot,'jane-b170-'));
  const dst=path.join(temp,'work',TARGET);
  fs.mkdirSync(path.dirname(dst),{recursive:true});
  if(fs.existsSync(dst))return hold('WORKSPACE_TARGET_ALREADY_EXISTS',repo);
  write(dst,change.after,{encoding:'utf8',flag:'wx'});
  const actual=read(dst,'utf8');
  record('PATCH_BYTES',actual===change.after,'Written bytes equal exact B168 proposal');
  record('PATCH_SHA256',digest(actual)===change.afterSha256,'Written content SHA-256 matches proof');
  record('FIXED_TEMPLATE',actual===TEMPLATE,'Only the canonical B161 template is permitted');
  record('ISSUE_TEMPLATE_FRONT_MATTER',actual.startsWith('---\n')&&actual.includes('\n---\n'),'Required YAML front matter present');
  record('REPRO_STEPS',actual.includes('## Steps to reproduce'),'Reproduction steps prompt present');
  record('EXPECTED_AND_ACTUAL',actual.includes('## Expected behavior')&&actual.includes('## Actual behavior'),'Expected/actual prompts present');
  record('SECRET_HYGIENE',actual.includes('Remove secrets'),'Redaction warning present');
  const all=checks.every(c=>c.status==='PASS');
  result={schema:'JANE-B170-ISOLATED-REPAIR-EVALUATION-v1',status:all?'LOCAL_CHECKS_PASS':'HOLD',
    repository:repo,mode:MODE,proposalSha256:proof.sha256,baseSha:e.base.commitSha,
    changesEvaluated:1,checks,requiredCheckNames:e.checks.expected,
    githubCiObserved:false,githubCiPassed:false,repositoryCodeExecuted:false,
    proposalTestsExecuted:true,localChecksPassed:all,
    mayCreatePR:false,mayMerge:false,mayRetry:false,defaultBranchWrites:false};
 }catch(err){result=hold('ISOLATED_EVALUATION_ERROR',repo)}
 finally{
  if(temp!==null){
   try{remove(temp,{recursive:true,force:true})}
   catch{result=hold('WORKSPACE_CLEANUP_FAILED',repo)}
  }
 }
 result.workspaceDeleted=temp!==null;
 return result;
}
function compile(records){
 if(!Array.isArray(records)||records.length>8)throw Error('INVALID_RECORD_COUNT');
 return{schema:'JANE-B170-EVALUATION-REPORT-v1',mode:'LOCAL_FIXED_TEMPLATE_ONLY',
  results:records,counts:{observed:records.length,localPassed:records.filter(x=>x.status==='LOCAL_CHECKS_PASS').length,
   held:records.filter(x=>x.status==='HOLD').length},
  governance:{oneObserverLayer:true,witnesses:['a1','b1','c1'],noQuorum:true,isaDefined:false,
   noRemoteCodeExecution:true,automaticWrites:false,autoMerge:false}};
}
function candidates(dir='ecosystem/proposals'){
 if(!fs.existsSync(dir))return[];
 const files=fs.readdirSync(dir,{withFileTypes:true}).filter(x=>x.isFile()&&/^[A-Za-z0-9_.-]+\.json$/.test(x.name))
  .map(x=>path.join(dir,x.name)).sort();
 if(files.length>8)throw Error('TOO_MANY_PROPOSALS');return files;
}
function main(){
 const argv=process.argv.slice(2),out=argv.includes('--output')?argv[argv.indexOf('--output')+1]:'ecosystem/reports/b170-latest.json';
 const dir=argv.includes('--dir')?argv[argv.indexOf('--dir')+1]:'ecosystem/proposals';
 if(!out||!dir)throw Error('PATH_REQUIRED');
 const rows=[];
 for(const name of candidates(dir)){
  try{rows.push(examine(JSON.parse(fs.readFileSync(name,'utf8'))))}
  catch{rows.push(hold('PROPOSAL_READ_ERROR'))}
 }
 const report=compile(rows);report.observation=rows.length?'LOCAL_VALIDATION':'HOLD_NO_PROPOSALS';
 fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({status:report.observation,counts:report.counts,githubCiObserved:false}));
}
if(require.main===module)try{main()}catch(e){console.error('HOLD '+e.message);process.exitCode=1}
module.exports={MODE,examine,hold,compile,candidates,digest};
