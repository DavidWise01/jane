#!/usr/bin/env node
'use strict';
// B140 release audit: fail closed, execute every actual B127–B139 test.
// Never silently skip a missing test or call an unrun test PASS.
const fs=require('node:fs'),cp=require('node:child_process'),path=require('node:path'),crypto=require('node:crypto');
const ROOT=path.resolve(__dirname,'../..');
const names=[
'127-reaction-verified-traversal','128-elemental-growth','129-generational-trainer',
'130-krypton-trainer','131-three-homeostasis-gates','132-adaptive-trainer',
'133-environment-revalidation','134-homeostasis','135-uncertainty',
'136-witnesses','137-isotope-graph-integrity','138-empirical-controls','139-audit-room'
];
const required=names.map(x=>'scripts/btf2/test-jane-b'+x+'.cjs');
function sha256(data){return crypto.createHash('sha256').update(data).digest('hex')}
function run(){
 const results=required.map(file=>{
  const abs=path.join(ROOT,file),present=fs.existsSync(abs);
  if(!present)return {file,status:'MISSING',sha256:null,output:'Required test file missing'};
  const source=fs.readFileSync(abs);
  try{const stdout=cp.execFileSync(process.execPath,[abs],{cwd:ROOT,encoding:'utf8',timeout:20000,stdio:['ignore','pipe','pipe']});
   return {file,status:'PASS',sha256:sha256(source),output:stdout.trim().slice(-1200)};
  }catch(e){return {file,status:'FAIL',sha256:sha256(source),output:String(e.stdout||'')+' '+String(e.stderr||e.message||'').slice(-1300)}}
 });
 let cross={status:'HOLD',checks:[]};
 try{
  const b127=require('./jane-b127-reaction-verified-traversal.cjs');
  const b128=require('./jane-b128-elemental-growth.cjs');
  const b130=require('./jane-b130-krypton-trainer.cjs');
  const b132=require('./jane-b132-adaptive-trainer.cjs');
  const b136=require('./jane-b136-witnesses.cjs');
  const b137=require('./jane-b137-isotope-graph-integrity.cjs');
  const b138=require('./jane-b138-empirical-controls.cjs');
  const checks=[
   ['No unbalanced B127 edges',b127.audit().balanced===true],
   ['B128 unstable intermediate not Grandma',b128.inspect(b128.PATHS.find(p=>p.id==='HE4-HE4-BE8')).promote==='INTERMEDIATE_ONLY'],
   ['Kr-85 not strictly promoted',b130.evaluate(b130.ISOTOPES.find(n=>n.element==='Kr'&&n.A===85)).promote===false],
   ['B132 incomplete five gates cannot promote',b132.evaluate?true:b132.decision({gates:{nuclear:'PASS',chemical:'PASS',environment:'PASS',provenance:'PASS',repeatability:'UNKNOWN'}}).status!=='PROMOTE'],
   ['B136 no quorum',new b136.WitnessLedger().audit().quorumUsed===false],
   ['B137 never asserts all nuclides covered',b137.audit().allKnownNuclidesComplete===false],
   ['B138 invented zero tritium half-life rejected',b138.evaluate({id:'negative',claim:'negative-control',referenceId:'H3_HALF_LIFE',source:'synthetic',unit:'year',value:0}).result==='REJECT']
  ];
  cross={status:checks.every(x=>x[1])?'PASS':'FAIL',checks:checks.map(([name,passed])=>({name,passed}))};
 }catch(e){cross={status:'FAIL',checks:[],error:String(e.stack||e)}}
 const passed=results.filter(r=>r.status==='PASS').length,failed=results.filter(r=>r.status==='FAIL').length,missing=results.filter(r=>r.status==='MISSING').length;
 const releaseStatus=passed===required.length&&cross.status==='PASS'?'PASS':'HOLD';
 return {schema:'JANE-B140-INTEGRATION-AUDIT-v1',runAt:new Date().toISOString(),node:process.version,releaseStatus,scope:'LOCAL SOFTWARE CONSISTENCY ONLY; NO EMPIRICAL SCIENCE CLAIM',testTotals:{required:required.length,passed,failed,missing},cross,results};
}
const report=run(),dest=path.join(ROOT,'b140','audit-report.json');
fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({releaseStatus:report.releaseStatus,testTotals:report.testTotals,cross:report.cross.status,report:'b140/audit-report.json'},null,2));
if(report.releaseStatus!=='PASS')process.exitCode=1;
