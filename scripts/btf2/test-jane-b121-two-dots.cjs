#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),B=require('./jane-b121-two-dots.cjs');
const s=B.audit(),members=B.pack();
assert.equal(s.dots,2);assert.equal(s.slots_per_dot,8);assert.equal(s.total_slots,16);
assert.deepEqual(s.coherence_pattern,[1,1,2,4,8]);
assert.equal(s.established,11);assert.equal(s.proposed,5);
assert.equal(new Set(members.map(m=>m.id)).size,16);
assert.equal(members.filter(m=>m.dot==='Q0').length,8);
assert.equal(members.filter(m=>m.dot==='Q1').length,8);
assert.deepEqual(B.dotAddress(0),{dot:'Q0',slot:0,binary:'000'});
assert.deepEqual(B.dotAddress(7),{dot:'Q0',slot:7,binary:'111'});
assert.deepEqual(B.dotAddress(8),{dot:'Q1',slot:0,binary:'000'});
assert.deepEqual(B.dotAddress(15),{dot:'Q1',slot:7,binary:'111'});
assert.throws(()=>B.dotAddress(16),/Slot out of range/);
console.log('PASS B121: 2 logical dots × 8 slots, 1|1|2|4|8, 11 established + 5 proposed, 16 stable addresses');
