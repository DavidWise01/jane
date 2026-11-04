#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const m=require('./jane-b144-common-frame.cjs');
const spec=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../b144/coordinate-frame-v1.json'),'utf8'));
assert.equal(m.validate(spec).status,'STRUCTURAL_PASS');
for(const ax of ['x','y','z']){
 assert.deepEqual(m.roundTrip([2,-1,5],ax,7),[2,-1,5]);
 assert.equal(m.normSquared(m.step([0,0,0],ax+'+',3)),9);
 assert.equal(m.normSquared(m.step([0,0,0],ax+'-',3)),9);
}
assert.deepEqual(m.translate([4,5,6],[1,2,3]),[3,3,3]);
assert.equal(m.normSquared([1,2,3]),14);
assert.throws(()=>m.step([0,0,0],'void+',1),/SIGNED_DIRECTION/);
assert.throws(()=>m.step([0,0,0],'x+',-1),/SIGNED_DIRECTION/);
const earth=m.schwarzschildStationaryRate({massKg:5.9722e24,radiusM:6378137});
assert.equal(earth.status,'REFERENCE_ONLY');
assert.ok(earth.ratio<1&&earth.ratio>0.999999999);
assert.ok(Math.abs((1-earth.ratio)-6.95e-10)<1e-11);
assert.equal(m.schwarzschildStationaryRate({}).status,'HOLD');
const radius=2*m.G*5.9722e24/(m.C*m.C);
assert.equal(m.schwarzschildStationaryRate({massKg:5.9722e24,radiusM:radius}).status,'HOLD');
const changed=JSON.parse(JSON.stringify(spec));changed.mappings.bodyToManifold='G0';assert.equal(m.validate(changed).status,'HOLD');
changed.mappings.bodyToManifold='UNASSIGNED';changed.coordinateFrame.directions['z-']=[0,0,1];assert.equal(m.validate(changed).status,'HOLD');
console.log('PASS B144: 6 signed movements, round-trip cancellation, squared symmetry, source-frame translation, stationary clock domain and unsupported mapping holds');
