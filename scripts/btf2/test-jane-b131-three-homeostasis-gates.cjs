#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),B=require('./jane-b131-three-homeostasis-gates.cjs');
const a=B.audit();
assert.equal(a.cases,6);
assert.equal(a.eligible,3);assert.equal(a.no_promotion,2);assert.equal(a.hold,1);
const get=id=>B.inspect(B.CASES.find(c=>c.id===id));
assert.equal(get('KR84-GAS-ROOM').decision,'ELIGIBLE');
assert.equal(get('KR85-GAS-ROOM').decision,'HOLD');
assert.equal(get('KRF2-ROOM').decision,'NO_PROMOTION');
assert.equal(get('KRF2-COLD').decision,'ELIGIBLE');
assert.equal(get('RB85-WATER').decision,'NO_PROMOTION');
assert.equal(get('RB85-ISOLATED').decision,'ELIGIBLE');
assert.equal(get('RB85-WATER').nuclear,'PASS');
assert.equal(get('KRF2-ROOM').N,48);
assert.equal(Object.keys(B.groupByNuclearIdentity()).length,3);
assert.throws(()=>B.inspect({id:'bad',Z:36,A:30}),/Invalid sourced candidate/);
console.log('PASS B131: 6 nuclear/chemical/environment records, 3 eligible, 2 reject, 1 hold');
