'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const m=require('./jane-b169-autonomous-scan.cjs');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'jane-b169-'));
(async()=>{
 try{
  assert.equal(m.candidates(dir).status,'HOLD_NO_PROPOSALS');
  const empty=await m.run({dir});assert.equal(empty.status,'HOLD_NO_PROPOSALS');
  assert.equal(empty.entries.length,0);assert.equal(empty.governance.automaticWrites,false);
  fs.writeFileSync(path.join(dir,'bad.json'),'{"status":"PROPOSAL_ONLY"}');
  const res=await m.run({dir});assert.equal(res.entries.length,1);
  assert.equal(res.entries[0].status,'HOLD');
  assert.equal(res.entries[0].mayCreatePR,false);
  for(let i=0;i<9;i++)fs.writeFileSync(path.join(dir,'bad-'+i+'.json'),'{}');
  assert.equal(m.candidates(dir).status,'HOLD_TOO_MANY_PROPOSALS');
  console.log('PASS B169 batch: missing proof HOLD, malformed proof HOLD, bounded autonomous read-only scan');
 }finally{fs.rmSync(dir,{force:true,recursive:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
