#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),K=require('./lilith-d003-kernel.cjs');
const a=K.audit(),cells=K.cells();
assert.deepEqual(a.profile,[1,3,6,6,3,1]);
assert.equal(a.cells,20);
assert.equal(a.unique_addresses,20);
assert.equal(a.layers,6);
assert.equal(a.outer_diameter,6);
assert.equal(a.linear_scale,0.5);
assert.equal(a.hole_radius,1.5);
for(const cell of cells){
 const r=Math.hypot(cell.x,cell.z);
 assert.ok(r>=a.hole_radius-1e-12&&r<=a.outer_diameter/2+1e-12);
 assert.ok(Math.abs((r-a.major_radius)**2+cell.y**2-a.minor_radius**2)<1e-10);
}
assert.throws(()=>K.torus(0,0,1,1),/Invalid/);
console.log('PASS D003: 20 cells, 6 exact bands, valid toroid, open hole, 50 percent Jane girth');
