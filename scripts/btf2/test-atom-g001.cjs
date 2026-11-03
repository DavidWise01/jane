#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),K=require('./atom-g001-kernel.cjs');
const s=K.audit(),cells=K.cells(),cycle=K.cycle();
assert.deepEqual(s.profile,[1,2,4,6,6,4,2,1]);
assert.equal(s.name,'a.t.o.m');
assert.equal(s.layers,8);assert.equal(s.cells,26);assert.equal(s.unique_ids,26);
assert.equal(s.mother_linear_scale,0.67);assert.equal(s.jane_linear_scale,0.335);
assert.ok(Math.abs(s.outer_diameter-4.02)<1e-12);
assert.ok(Math.abs(s.hole_radius-1.005)<1e-12);
assert.equal(cycle.length,26);assert.equal(cycle[25].next,cycle[0].id);
for(const c of cells){const radial=Math.hypot(c.x,c.z);assert.ok(radial>=s.hole_radius-1e-12);assert.ok(Math.abs((radial-s.major_radius)**2+c.y*c.y-s.minor_radius**2)<1e-10)}
assert.throws(()=>K.point(0,0,1,1),/Invalid/);
console.log('PASS a.t.o.m G001: 8 bands, 26 cells, 67% Lilith, 33.5% Jane, toroid hole, cyclic traversal');
