#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),m=require('./jane-b127-reaction-verified-traversal.cjs');
let result=m.audit();assert.equal(result.verified_records,4);
assert.equal(result.balanced,true);
assert.equal(result.be7_unstable_intermediate,true);
assert.equal(m.isotopeRecord(1,3,'radioactive','source').N,2);
assert.equal(m.isotopeRecord(2,4,'stable','source').N,2);
assert.throws(()=>m.isotopeRecord(2,1),/Invalid nuclear address/);
for(const r of m.REACTIONS){const c=m.evaluate(r);assert.equal(c.balanced,true);assert.equal(c.validPromote,true);}
let fake={id:'FAKE',reactants:['H2'],products:['He4'],promote:'Helium',evidence:'none'};
assert.equal(m.evaluate(fake).balanced,false);
assert.equal(m.REACTIONS[2].promote,null);
assert.deepEqual(m.REFERENCES.map(x=>x.Z),[1,2,3,4]);
console.log('PASS B127: nuclear A, charge, and lepton conservation; stable-product grandma handoff; unbound catalogue boundaries');
