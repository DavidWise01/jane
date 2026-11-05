'use strict';
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict');
const {candidates,run}=require('./jane-b174-autonomous-manifest.cjs');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'jane-b174-list-'));
(async()=>{
 try{
  assert.equal(candidates(dir).length,0);
  const empty=await run({dir});assert.equal(empty.status,'HOLD_NO_PROPOSALS');
  assert.equal(empty.counts.exactDelta,0);
  fs.writeFileSync(path.join(dir,'invalid.json'),'{"status":"PROPOSAL_ONLY"}');
  const invalid=await run({dir});assert.equal(invalid.entries[0].status,'HOLD');
  assert.equal(invalid.entries[0].mayCreatePR,false);
  for(let i=0;i<8;i++)fs.writeFileSync(path.join(dir,'extra'+i+'.json'),'{}');
  assert.throws(()=>candidates(dir),/TOO_MANY_PROPOSALS/);
  console.log('PASS B174 runner: no proposal is HOLD, malformed proof HOLD, 8-max, no PR permission');
 }finally{fs.rmSync(dir,{force:true,recursive:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
