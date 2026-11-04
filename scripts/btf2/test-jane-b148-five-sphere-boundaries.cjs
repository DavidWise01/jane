#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const m=require('./jane-b148-five-sphere-boundaries.cjs');
const d=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../b148/five-spheres-v1.json'),'utf8'));
assert.equal(m.validate(d).status,'STRUCTURAL_PASS_WITH_UNBOUND_SPHERES');
const out=m.evaluateTransition(d,'S1','+',{frame:'Earth',time:'2026-11-04T00:00:00Z',source:'synthetic'});
assert.equal(out.status,'HOLD');
assert.equal(m.evaluateTransition(d,'S1','+',{}).status,'HOLD');
function negative(fn){const x=JSON.parse(JSON.stringify(d));fn(x);assert.equal(m.validate(x).status,'HOLD')}
negative(x=>x.primaryShadow.onlyShadowPair=false);
negative(x=>x.primaryShadow.foldedPositions=0);
negative(x=>x.signedSphereSlots.pop());
negative(x=>x.signedSphereSlots[0].physicalRegionId='IONOSPHERE');
negative(x=>x.signedSphereSlots[1].transitionRule='CROSS');
negative(x=>x.physicalExamples[2].outerKm=1000000);
negative(x=>x.physicalExamples[0].innerKm=1000);
negative(x=>x.physicalExamples[4].source='none');
negative(x=>x.modelBodyOrder.reverse());
negative(x=>x.gravitationalClockRate=0.5);
console.log('PASS B148: one shadow, five signed unbound slots, five independently sourced candidate spheres, ten mutation failures');
