#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {audit}=require('./jane-b146-uploaded-distance-audit.cjs');
const d=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../b146/distance-gravity-source-v1.json'),'utf8'));
const r=audit(d);assert.equal(r.status,'SOURCE_STRUCTURE_PASS_WITH_CONFLICT');assert.equal(r.vertexEdges,5);assert.equal(r.sourceEdges,6);assert.equal(r.physicalClockRate,'HOLD');
function change(fn){let c=JSON.parse(JSON.stringify(d));fn(c);assert.equal(audit(c).status,'HOLD');}
change(x=>x.fields[0].kind='void');change(x=>x.userEdges[0].nonzeroGap=false);
change(x=>x.measuredSeparationMeters=123);change(x=>x.bodyOrder.reverse());
change(x=>x.status='PASS');change(x=>x.userEdges[3].to='NIB SUN');
console.log('PASS B146: uploaded original six connections preserved; four vertices; one nested Earth link; topology discrepancy held; six corruption controls');
