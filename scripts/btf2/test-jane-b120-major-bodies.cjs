#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),B=require('./jane-b120-major-bodies.cjs');
const a=B.audit();
assert.equal(a.body_count,4);assert.equal(a.orbiting_bodies,3);
assert.equal(a.cell_count,188);assert.deepEqual(a.cell_counts,[66,60,42,20]);
assert.deepEqual(a.names,['Jane','Toph','Patricia','Lilith']);
assert.equal(a.descendants_rendered,0);assert.equal(a.hard_stop,true);
for(const t of [0,1,10,100]){const q=B.orbit(t);
 assert.equal(q.length,4);
 for(let i=2;i<4;i++)assert.ok(Math.abs(q[i].phase-q[i-1].phase-B.TAU/3)<1e-10);
 for(let i=1;i<4;i++)assert.ok(Math.abs(Math.hypot(q[i].center.x,q[i].center.z)-13.5)<1e-10);
}
const ids=B.BODY_SPECS.flatMap(x=>B.lattice(x).map(y=>y.id));
assert.equal(new Set(ids).size,188);
assert.throws(()=>B.orbit(NaN),/Invalid time/);
console.log('PASS B120: Jane + three major bodies, 188 unique cells, 120° phase, safe envelope, zero descendants');
