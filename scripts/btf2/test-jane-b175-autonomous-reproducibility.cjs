'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const {files,scan}=require('./jane-b175-autonomous-reproducibility.cjs');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'b175-autonomous-'));
(async()=>{
 try{
  assert.deepEqual(files(dir),[]);
  const empty=await scan({dir});assert.equal(empty.status,'HOLD_NO_PROPOSALS');
  assert.equal(empty.counts.reproducible,0);
  fs.writeFileSync(path.join(dir,'invalid.json'),'{"status":"PROPOSAL_ONLY"}');
  const rejected=await scan({dir});assert.equal(rejected.results[0].status,'HOLD');
  assert.equal(rejected.results[0].mayMerge,false);
  for(let n=0;n<8;n++)fs.writeFileSync(path.join(dir,'extra'+n+'.json'),'{}');
  assert.throws(()=>files(dir),/TOO_MANY_PROPOSALS/);
  console.log('PASS B175 bounded scan: no proofs HOLD, malformed proof HOLD, no write authority, cap eight');
 }finally{fs.rmSync(dir,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
