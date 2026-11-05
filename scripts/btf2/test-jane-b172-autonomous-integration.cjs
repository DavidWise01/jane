'use strict';
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict');
const {files,run}=require('./jane-b172-autonomous-integration.cjs');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'jane-b172-batch-'));
(async()=>{
 try{
  assert.equal(files(dir).length,0);
  const empty=await run({dir});assert.equal(empty.status,'HOLD_NO_PROPOSALS');
  assert.equal(empty.counts.passed,0);assert.equal(empty.governance.automaticWrites,false);
  fs.writeFileSync(path.join(dir,'invalid.json'),'{"status":"PROPOSAL_ONLY"}');
  const rejected=await run({dir});assert.equal(rejected.counts.held,1);
  assert.equal(rejected.results[0].mayCreatePR,false);
  for(let i=0;i<8;i++)fs.writeFileSync(path.join(dir,'excess'+i+'.json'),'{}');
  assert.throws(()=>files(dir),/HOLD_TOO_MANY_PROPOSALS/);
  console.log('PASS B172 autonomous batch: missing proposal HOLD, invalid proof HOLD, 8-cap, no write authority');
 }finally{fs.rmSync(dir,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
