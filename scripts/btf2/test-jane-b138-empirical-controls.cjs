#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict');const {REFERENCES,evaluate,EvidenceJournal}=require('./jane-b138-empirical-controls.cjs');
const j=new EvidenceJournal();
function check(id,referenceId,value,unit,expected){const r=j.submit({id,referenceId,value,unit,claim:'synthetic regression comparison',source:'explicit test fixture'});assert.equal(r.result,expected,id);return r;}
check('H3-REFERENCE','H3_HALF_LIFE',12.32,'year','PASS');
check('H3-NEGATIVE','H3_HALF_LIFE',0,'year','REJECT');
check('H3-LOW','H3_HALF_LIFE',12.30,'year','PASS');
check('DT-REFERENCE','DT_FUSION_Q',17.60,'MeV','PASS');
check('DT-NEGATIVE','DT_FUSION_Q',100,'MeV','REJECT');
check('DT-UNIT','DT_FUSION_Q',17.60,'year','HOLD');
check('KR-REFERENCE','KR84_STATUS','STABLE','nuclear_status','PASS');
check('KR-NEGATIVE','KR84_STATUS','RADIOACTIVE_10_YEAR','nuclear_status','REJECT');
check('UNSOURCED','UNKNOWN_REFERENCE',9,'MeV','HOLD');
assert.equal(evaluate({id:'bad',referenceId:'H3_HALF_LIFE',value:NaN,unit:'year',claim:'bad',source:'x'}).result,'HOLD');
assert.throws(()=>check('H3-REFERENCE','H3_HALF_LIFE',12.32,'year','PASS'),/Duplicate/);
assert.deepEqual(j.audit(),{claims:9,pass:4,reject:3,hold:2,chainVerified:true});
assert.equal(REFERENCES['DT_FUSION_Q'].value,17.6);
console.log('PASS B138: 9 reference-control fixtures; 4 PASS, 3 REJECT, 2 HOLD; immutable chain');
