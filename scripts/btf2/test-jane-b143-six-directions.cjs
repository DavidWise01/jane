#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const v=require('./jane-b143-six-directions.cjs');
const d=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../b143/six-directions-v1.json'),'utf8'));
assert.equal(v.validate(d).ok,true);
const mutation=(fn)=>{const x=JSON.parse(JSON.stringify(d));fn(x);assert.equal(v.validate(x).state,'HOLD')};
mutation(x=>x.directions.pop());
mutation(x=>x.directions[1].sign=1);
mutation(x=>x.axes[2].square='z');
mutation(x=>x.axes[2].delimiter=',');
mutation(x=>x.manifolds[3].kind='gravity');
mutation(x=>x.bodySequence.reverse());
mutation(x=>x.bodyToDirection={earth:'+x'});
mutation(x=>x.physicalMetric='VERIFIED');
assert.equal(new Set(d.directions.map(x=>x.axis)).size,3);
assert.equal(new Set(d.directions.map(x=>x.id)).size,6);
console.log('PASS B143: signed six directions, squared 3 axes, preserved four manifolds/five bodies, eight negative controls');
