#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),C=require('./jane-b1221-codon-correction.cjs');
const a=C.audit();
assert.equal(a.codon_positions,64);assert.equal(a.analytical_cubits_per_codon,8);
assert.equal(a.two_cubits,16);assert.equal(a.fraction,.25);
assert.equal(C.triplet(0),'AAA');assert.equal(C.triplet(63),'TTT');
assert.equal(new Set(Array.from({length:64},(_,i)=>C.triplet(i))).size,64);
for(let i=0;i<4;i++)assert.equal(C.quarter(i).length,16);
assert.equal(C.address(16).quarter,1);assert.equal(C.address(63).cubit,7);
assert.throws(()=>C.address(64),/out of range/);
console.log('PASS B122.1: 4^3=64, 8 cubits, 2 cubits=quarter codon, 16/20 choices retained');
