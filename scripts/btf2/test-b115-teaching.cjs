#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),C=require('./b115-teaching-core.cjs');
const ev=(id,repo,field)=>({id,repo,field,previous_run:'r1',current_run:'r2'});
const b114={patterns:[{field:'archived',observed_transitions:2,distinct_repositories:2}],evidence:[ev('a','DavidWise01/first','archived'),ev('b','DavidWise01/second','archived')]};
const family={members:[{repo:'DavidWise01/first',channel:'btf2:davidwise01/first',generation:'ARRIVAL_2026-11-03'},{repo:'DavidWise01/second',generation:'UNKNOWN'},{repo:'DavidWise01/third',generation:'UNKNOWN'}]};
const first=C.build(b114,family);
assert.equal(first.cards.length,1);assert.equal(first.cards[0].level,'RECURRING_METADATA_OBSERVATION');assert.equal(first.newEvents.length,1);
assert.equal(first.suggestions.length,2);assert.equal(first.suggestions.every(x=>x.mode==='AVAILABLE_NOT_SENT'),true);
const second=C.build(b114,family,{cards:first.cards});assert.equal(second.newEvents.length,0);assert.equal(second.cards[0].lesson_id,first.cards[0].lesson_id);
const extra=C.build({...b114,evidence:[...b114.evidence,ev('c','DavidWise01/third','archived')]},family,{cards:first.cards});assert.equal(extra.newEvents.length,1);assert.notEqual(extra.cards[0].lesson_id,first.cards[0].lesson_id);
const noRegistry=C.build(b114);assert.equal(noRegistry.suggestions.length,0);
assert.throws(()=>C.build({patterns:[]}),/Requires B114/);
console.log('PASS B115: provenance IDs, repeat-run idempotence, version by evidence, optional delivery, missing family safe');
