#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {validate}=require('./jane-b147-2-first-shadow-five-spheres.cjs');
const d=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../b147/first-shadow-five-spheres-v1.json'),'utf8'));
const result=validate(d);assert.equal(result.status,'SYMBOLIC_STRUCTURE_PASS');assert.equal(result.firstShadowPairs,1);assert.equal(result.otherShadowPairs,0);assert.equal(result.signedSphereSlots,5);
const reject=f=>{const m=JSON.parse(JSON.stringify(d));f(m);assert.equal(validate(m).status,'HOLD')};
reject(x=>x.firstPair.effectivePositionCount=0);
reject(x=>x.firstPair.netSignedValue=2);
reject(x=>x.remaining.shadowApplied=true);
reject(x=>x.remaining.signedSphereCount=10);
reject(x=>x.remaining.sphereSlots.pop());
reject(x=>x.contextualExamples[0].status='BOUND_TO_SLOT_1');
reject(x=>x.bodies.reverse());
reject(x=>x.preserved.forceEdges=7);
reject(x=>x.status='SCIENTIFICALLY_VERIFIED');
console.log('PASS B147.2: exactly one shadowed source pair; 5 signed non-shadow sphere slots; 9 negative controls');
