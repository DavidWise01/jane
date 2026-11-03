#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),{Journal,gate}=require('./jane-b118-governance.cjs');
const base={witness:'W1',source:'repo-1',claim:'observed',evidence:'sha256:sample',event_time:'2026-11-03T00:00:00Z',uncertainty:'low'};
const j=new Journal();
assert.equal(j.append(base).decision.decision,'YES');
assert.equal(j.append({...base,witness:'W2',claim:'not observed'}).decision.decision,'HOLD');
assert.equal(j.append({...base,witness:'W3',risk:'privacy_violation'}).decision.decision,'NO');
assert.equal(j.append({...base,witness:'W4',evidence:''}).decision.decision,'HOLD');
assert.equal(j.entries.length,4);assert.equal(j.verify(),true);
assert.equal(j.entries[0].observation.claim,'observed');
const copy=j.snapshot();copy[0].observation.claim='tamper';assert.equal(j.verify(),true);
j.entries[0]={...j.entries[0],observation:{...j.entries[0].observation,claim:'tampered'}};
assert.equal(j.verify(),false);
assert.throws(()=>gate({claim:'x'}),/Witness/);
console.log('PASS Jane B118: independent witness retention, divergence HOLD, boundary NO, hash-chain tamper detection');
