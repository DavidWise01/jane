#!/usr/bin/env node
'use strict';
const A=require('node:assert/strict'),G=require('./b113-generation-core.cjs');
A.equal(G.cohort('2026-11-03T12:00:00Z'),'ARRIVAL_2026-11-03');
A.equal(G.cohort('bad'),'UNKNOWN');
const seed=[{repo:'DavidWise01/a',formic:'FORMIC-A',q:0,r:0,first_seen:'2026-11-01T12:00:00Z'},
{repo:'DavidWise01/b',formic:'FORMIC-B',q:1,r:0,first_seen:'2026-11-02T12:00:00Z'}];
const a=G.normalize(seed,{},'2026-11-03T00:00:00Z');
A.equal(a.events.length,2);A.equal(a.members[0].generation,'ARRIVAL_2026-11-01');A.equal(a.members[0].lineage.parentage,'UNKNOWN');
const previous=Object.fromEntries(a.members.map(x=>[x.repo.toLowerCase(),x]));
const b=G.normalize([...seed,{repo:'DavidWise01/c',first_seen:'2026-11-03T12:00:00Z'}],previous,'2026-11-04T00:00:00Z');
A.equal(b.events.length,1);A.equal(b.members[0].generation,a.members[0].generation);A.equal(b.members[2].lineage.parentage,'UNKNOWN');
const changed=G.normalize([{...seed[0],first_seen:'2026-11-10T00:00:00Z'}],previous);A.equal(changed.members[0].first_seen,seed[0].first_seen);
const many=G.normalize(Array.from({length:2147},(_,i)=>({repo:'DavidWise01/r'+i})));
A.equal(many.members.length,2147);A.equal(many.members.every(x=>x.generation==='UNKNOWN'),true);
console.log('PASS: idempotency, 2147 family members, no invented ancestry, stable cohorts');
