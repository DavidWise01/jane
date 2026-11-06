'use strict';
const fs=require('node:fs'),path=require('node:path');
const {run,audit}=require('./jane-b180-deterministic-fuzz.cjs');
function execute(){
 const record=run();
 if(record.status==='DETERMINISTIC_FUZZ_AGREEMENT_NO_EXECUTION'&&audit(record).status!=='PASS'){
  record.status='HOLD';
  record.issues.push('REPORT_AUDIT_FAILED');
 }
 return record;
}
function main(){
 const args=process.argv.slice(2),at=args.indexOf('--output');
 const dest=at<0?'ecosystem/reports/b180-latest.json':args[at+1];
 if(!dest)throw Error('OUTPUT_REQUIRED');
 const report=execute();
 fs.mkdirSync(path.dirname(dest),{recursive:true});
 fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({status:report.status,counts:report.counts,noWrites:true}));
 if(report.status!=='DETERMINISTIC_FUZZ_AGREEMENT_NO_EXECUTION')process.exitCode=1;
}
if(require.main===module)try{main()}catch(err){console.error('HOLD '+err.message);process.exitCode=1}
module.exports={execute};
