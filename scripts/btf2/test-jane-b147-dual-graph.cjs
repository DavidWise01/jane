#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict');const m=require('./jane-b147-dual-graph.cjs');
const d=m.build(),r=m.audit(d);
assert.equal(r.status,'STRUCTURAL_PASS_WITH_UNBOUND_EDGE');assert.equal(r.forceEdges,6);assert.equal(r.geometricPairs,6);assert.equal(r.matched,5);assert.deepEqual(r.unbound,[['nib sun','earth']]);
assert.equal(d.force.find(e=>e.id==='u4').from,'earth');assert.equal(d.force.find(e=>e.id==='u4').to,'earth sun');
assert.equal(d.geometry.find(e=>e.from==='nib sun'&&e.to==='earth').sourceForceId,null);
const negative=fn=>{const x=JSON.parse(JSON.stringify(d));fn(x);assert.equal(m.audit(x).status,'HOLD')};
negative(x=>x.order.reverse());negative(x=>x.force[3].to='earth');negative(x=>x.force[5].distanceBand='measured');negative(x=>x.geometry[4].distanceMeters=100);negative(x=>x.geometry[4].sourceForceId='invented');negative(x=>x.physicalStatus='PASS');negative(x=>x.missing=[]);
assert.equal(d.geometry.filter(e=>e.sourceForceId===null).length,1);
console.log('PASS B147: six force connections preserved, six geometric pairs independently enumerated, five overlaps, one unbound pair, seven negative controls');
