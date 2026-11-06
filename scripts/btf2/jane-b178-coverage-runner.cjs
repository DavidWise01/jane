'use strict';
/** B178 deterministic semantic constraint matrix; zero network and GitHub mutations. */
const fs=require('node:fs'),path=require('node:path');
const {run,audit}=require('./jane-b178-constraint-coverage.cjs');
function execute(){
 const report=run();
 if(report.status==='CONSTRAINT_COVERAGE_PASS_NO_EXECUTION'&&audit(report).status!=='PASS'){
  report.status='HOLD';report.errors.push('ATTESTATION_VERIFICATION_FAILED');
 }
 return report;
}
function main(){
 const argv=process.argv.slice(2),i=argv.indexOf('--output');
 const output=i<0?'ecosystem/reports/b178-latest.json':argv[i+1];
 if(!output)throw Error('OUTPUT_REQUIRED');
 const result=execute();
 fs.mkdirSync(path.dirname(output),{recursive:true});
 fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({status:result.status,observed:result.observed,issues:result.errors.length,
  noWrites:true,notTargetRepositoryCI:true}));
 if(result.status!=='CONSTRAINT_COVERAGE_PASS_NO_EXECUTION')process.exitCode=1;
}
if(require.main===module)main();
module.exports={execute};
