'use strict';
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict');
const {candidates,run}=require('./jane-b173-autonomous-tree.cjs');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'jane-b173-batch-'));
(async()=>{
 try{
  assert.equal(candidates(dir).length,0);
  const empty=await run({dir});assert.equal(empty.status,'HOLD_NO_PROPOSALS');
  fs.writeFileSync(path.join(dir,'invalid.json'),'{"status":"PROPOSAL_ONLY"}');
  const rejected=await run({dir});assert.equal(rejected.counts.held,1);
  assert.equal(rejected.results[0].mayCreatePR,false);
  for(let i=0;i<8;i++)fs.writeFileSync(path.join(dir,'extra'+i+'.json'),'{}');
  assert.throws(()=>candidates(dir),/TOO_MANY_PROPOSALS/);
  console.log('PASS B173 autonomous: no proof HOLD, invalid proof HOLD, bounded scan, no write privileges');
 }finally{fs.rmSync(dir,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
