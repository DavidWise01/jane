'use strict';
/** B177 bounded semantic inspection of the B176 live differential evidence. */
const fs=require('node:fs'),path=require('node:path');
const {files,scan}=require('./jane-b176-autonomous-differential.cjs');
const {inspect,audit,registry,hold}=require('./jane-b177-semantic-template.cjs');
async function run({dir='ecosystem/proposals',token='',scanFn=scan}={}){
 const names=files(dir);
 const observed=await scanFn({dir,token});
 if(!Array.isArray(observed?.results)||observed.results.length!==names.length)
  throw Error('B176_RESULT_COUNT_MISMATCH');
 const results=[];
 for(let i=0;i<names.length;i++){
  let proof;try{proof=JSON.parse(fs.readFileSync(names[i],'utf8'))}
  catch{results.push(hold('INVALID_PROOF_FILE'));continue}
  let record;
  try{record=inspect(proof,observed.results[i])}
  catch{record=hold('B177_SEMANTIC_EXCEPTION',proof)}
  if(record.status==='SEMANTICALLY_VALID_FIXED_TEMPLATE_NO_EXECUTION'&&audit(record).status!=='PASS')
   record=hold('B177_ATTESTATION_AUDIT_FAILED',proof);
  results.push(record);
 }
 return registry(results);
}
async function main(){
 const argv=process.argv.slice(2),i=argv.indexOf('--output');
 const output=i<0?'ecosystem/reports/b177-latest.json':argv[i+1];
 if(!output)throw Error('OUTPUT_REQUIRED');
 const result=await run({token:process.env.GITHUB_TOKEN||''});
 fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({status:result.status,counts:result.counts,writeAuthority:false}));
}
if(require.main===module)main().catch(e=>{console.error('HOLD '+e.message);process.exitCode=1});
module.exports={run};
