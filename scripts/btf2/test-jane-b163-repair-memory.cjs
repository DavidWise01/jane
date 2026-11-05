'use strict';
const assert=require('node:assert/strict');
const {classify,build,audit,suppression}=require('./jane-b163-repair-memory.cjs');
const make=(repo,decision,extras={})=>({repo:'DavidWise01/'+repo,decision,...extras});
const input={schema:'JANE-B162-FORMIC-PR-VERIFICATION-v1',owner:'DavidWise01',mode:'READ_ONLY',
 observedAt:'2026-11-05T09:00:00Z',results:[
  make('failed','HOLD_CHECKS_FAILED',{pr:{number:4,headSha:'deadbeef'},checks:{state:'HOLD_CHECKS_FAILED',failed:['ci:test']}}),
  make('green','REVIEW_READY_NO_AUTO_MERGE',{pr:{number:3,headSha:'cafed00d'},checks:{state:'CHECKS_REPORTED_SUCCESS'}}),
  make('closed','HOLD_CLOSED_PR_RETRY_SUPPRESSED',{pr:{number:2,state:'closed'}}),
  make('untried','NO_FORMIC_PR'),
  make('pending','HOLD_CHECKS_PENDING'),
  make('unknown','HOLD_CHECKS_UNAVAILABLE')
 ]};
const b=build(input);
assert.equal(audit(b).status,'PASS');
assert.equal(b.events.length,6);
assert.equal(b.counts.failed,1);assert.equal(b.counts.green,1);assert.equal(b.counts.closedSuppressed,1);
assert.equal(suppression(b,'DavidWise01/failed').decision,'SUPPRESS_REPAIR');
assert.equal(suppression(b,'DavidWise01/closed').decision,'SUPPRESS_REPAIR');
assert.equal(suppression(b,'DavidWise01/green').decision,'NO_AUTOMATIC_AUTHORIZATION');
assert.equal(suppression(b,'DavidWise01/untried').decision,'NO_AUTOMATIC_AUTHORIZATION');
assert.equal(suppression(b,'SomebodyElse/repo').decision,'HOLD_INVALID_SCOPE');
assert.equal(classify(make('x','SOMETHING_NEW')).state,'HOLD_UNKNOWN_DECISION');
assert.deepEqual(build(input),b);
assert.equal(b.events[0].evidence.repo,'DavidWise01/closed');
let tamper=JSON.parse(JSON.stringify(b));tamper.events[2].evidence.state='CHECKS_GREEN';
assert.equal(audit(tamper).status,'HOLD');
tamper=JSON.parse(JSON.stringify(b));tamper.events.reverse();
assert.equal(audit(tamper).status,'HOLD');
assert.throws(()=>build({...input,results:[make('x','NO_FORMIC_PR'),make('x','NO_FORMIC_PR')]}),/DUPLICATE/);
assert.throws(()=>build({...input,results:[make('x','NO_FORMIC_PR'),{repo:'someoneelse/private',decision:'NO_FORMIC_PR'}]}),/OUT_OF_SCOPE/);
assert.throws(()=>build({...input,mode:'WRITE'}),/INVALID/);
console.log('PASS B163 stable PR-history repair memory, failure suppression, green check never authorizes merge, duplicate/tamper detection');
