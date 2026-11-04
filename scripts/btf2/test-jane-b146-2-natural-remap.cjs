#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {inspect}=require('./jane-b146-2-natural-remap.cjs');
const d=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../b146/natural-remap-v1.json'),'utf8'));
const r=inspect(d);assert.equal(r.status,'REMAP_STRUCTURE_PASS');assert.equal(r.coreEdges,5);assert.equal(r.terminalEdges,1);assert.deepEqual(r.missingCoreEdges,['earth|nib sun']);
const mutate=f=>{const clone=JSON.parse(JSON.stringify(d));f(clone);assert.equal(inspect(clone).status,'HOLD')};
mutate(x=>x.canonicalOrder[3]='earth sun');
mutate(x=>x.edges[3].from='earth sun');
mutate(x=>x.edges[5].to='earth sun');
mutate(x=>x.edges[1].notation='z²');
mutate(x=>x.manifolds[2].kind='gravity');
mutate(x=>x.distanceValuesMeters=1);
mutate(x=>x.tetrahedron.resolution='ASSIGNED');
mutate(x=>x.clockPrediction=1);
console.log('PASS B146.2: six preserved slots, canonical corrected order, five core edges plus one terminal, missing core pair remains HOLD, eight negative controls');
