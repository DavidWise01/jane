'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {run}=require('./jane-b177-autonomous-semantic.cjs');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'jane-b177-'));
(async()=>{
 try{
  const empty=await run({dir,scanFn:async()=>({results:[]})});
  assert.equal(empty.status,'HOLD_NO_PROPOSALS');
  fs.writeFileSync(path.join(dir,'invalid.json'),'{"status":"PROPOSAL_ONLY"}');
  const held=await run({dir,scanFn:async()=>({results:[{status:'HOLD'}]})});
  assert.equal(held.results[0].status,'HOLD');
  assert.equal(held.results[0].mayCreatePR,false);
  await assert.rejects(()=>run({dir,scanFn:async()=>({results:[]})}),/RESULT_COUNT/);
  console.log('PASS B177: missing proofs HOLD, malformed proofs HOLD, evidence count mismatch HOLD');
 }finally{fs.rmSync(dir,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
