'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {files,scan}=require('./jane-b176-autonomous-differential.cjs');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'b176-scan-'));
(async()=>{
 try{
  assert.deepEqual(files(dir),[]);
  const empty=await scan({dir});
  assert.equal(empty.status,'HOLD_NO_PROPOSALS');
  assert.equal(empty.governance.automaticWrites,false);
  fs.writeFileSync(path.join(dir,'invalid.json'),'{"status":"PROPOSAL_ONLY"}');
  const rejected=await scan({dir});assert.equal(rejected.results[0].status,'HOLD');
  assert.equal(rejected.results[0].mayCreatePR,false);
  for(let i=0;i<8;i++)fs.writeFileSync(path.join(dir,'extra'+i+'.json'),'{}');
  assert.throws(()=>files(dir),/TOO_MANY_PROPOSALS/);
  console.log('PASS B176 autonomous: no proof HOLD; malformed proof HOLD; eight-max; no writes');
 }finally{fs.rmSync(dir,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
