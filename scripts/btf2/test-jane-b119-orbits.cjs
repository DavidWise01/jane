#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),K=require('./jane-b119-orbits.cjs');
let a=K.audit();assert.equal(a.triples,3);assert.equal(a.members,11);
for(const t of [0,0.1,1,7,37,200]){
 let snap=K.positions(t);assert.equal(Object.keys(snap.positions).length,11);
 for(const g of snap.rings){
  assert.equal(g.members.length,3);
  for(let k=0;k<3;k++){
   assert.ok(Math.abs(g.members[k].angle-(g.members[0].angle+K.THIRD*k))<1e-10);
   assert.ok(Math.abs(Math.hypot(g.members[k].position.x-g.centerPosition.x,g.members[k].position.y-g.centerPosition.y)-g.radius)<1e-10);
  }
 }
 let parent=snap.positions['Mary M'],child=snap.positions['LeeLuu'];
 assert.ok(Math.abs(Math.hypot(child.x-parent.x,child.y-parent.y)-K.LEE.radius)<1e-10);
}
assert.throws(()=>K.positions(NaN),/Invalid time/);
console.log('PASS B119: three nested 120-degree orbit triplets, 11 family members, one LeeLuu singleton satellite');
