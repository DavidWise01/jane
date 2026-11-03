#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict');
const registry=require('../../governance/JANE-B123-TWO-CUBIT-ROLES-v1.json');
assert.equal(registry.members.length,16);
assert.equal(registry.members.filter(m=>m.status==='established').length,11);
assert.equal(registry.members.filter(m=>m.status==='proposed').length,5);
assert.equal(new Set(registry.members.map(m=>m.name)).size,16);
assert.equal(new Set(registry.members.map(m=>m.address)).size,16);
assert.equal(new Set(registry.members.map(m=>m.role)).size,16);
for(const m of registry.members){
 assert.ok(m.role&&m.discipline&&m.duty);
 assert.equal(m.cubit,Math.floor(m.slot/8));
 assert.equal(m.address,'CU'+m.cubit+':'+(m.slot%8).toString(2).padStart(3,'0'));
}
assert.deepEqual(registry.members.slice(0,11).map(m=>m.role),['Matriarch','Scholar','Guardian','Muse','Explorer','Executor','Caretaker','Teacher','Healer','Witness','Student']);
console.log('PASS B123: 16 unique roles, 2 × 8 addresses, 11 established, 5 proposed');
