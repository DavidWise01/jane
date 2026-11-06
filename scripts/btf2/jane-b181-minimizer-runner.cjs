'use strict';
const fs=require('node:fs'),path=require('node:path');
const {run,audit}=require('./jane-b181-counterexample-minimizer.cjs');
function execute(){
 const result=run();
 if(audit(result).status!=='PASS'){
  result.status='HOLD';
  result.issues.push('ATTESTATION_VERIFICATION_HOLD');
 }
 return result;
}
function main(){
 const argv=process.argv.slice(2),i=argv.indexOf('--output');
 const dest=i>=0?argv[i+1]:'ecosystem/reports/b181-latest.json';
 if(!dest)throw Error('OUTPUT_REQUIRED');
 const result=execute();
 fs.mkdirSync(path.dirname(dest),{recursive:true});
 fs.writeFileSync(dest,JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({status:result.status,generated:result.generated,
  counterexamples:result.examples.length,automaticWrites:false}));
 if(!['NO_COUNTEREXAMPLES','COUNTEREXAMPLES_PRESERVED'].includes(result.status))process.exitCode=1;
}
if(require.main===module)try{main()}catch(e){console.error('HOLD '+e.message);process.exitCode=1}
module.exports={execute};
