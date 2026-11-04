#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),m=require('./jane-b142-four-manifold-boundary.cjs');
const d=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../b142/four-manifold-boundary-v1.json'),'utf8'));
assert.deepEqual(m.validate(d),{ok:true,status:'STRUCTURAL_PASS_ONLY',errors:[]});
const mutate=fn=>{const c=JSON.parse(JSON.stringify(d));fn(c);return m.validate(c)};
assert.equal(mutate(x=>x.container.manifolds[3].kind='gravity').status,'HOLD');
assert.equal(mutate(x=>x.bodySequence[1].label='Nibiru').status,'HOLD');
assert.equal(mutate(x=>x.bodyToManifold='ASSIGNED').status,'HOLD');
assert.equal(mutate(x=>x.notation='-+').status,'HOLD');
assert.equal(mutate(x=>x.container.polarity=['+','-']).status,'HOLD');
assert.equal(mutate(x=>x.gravitationalGeometry='VERIFIED').status,'HOLD');
console.log('PASS B142 geometry boundary: 4 manifolds, 2 gravity, 2 void, 5 unchanged referents, signed polarity; unknowns HOLD');
