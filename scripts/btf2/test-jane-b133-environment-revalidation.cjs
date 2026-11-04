#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict');
const {Trainer}=require('./jane-b133-environment-revalidation.cjs');
const t=new Trainer();
const pass={nuclear:'PASS',chemical:'PASS',environment:'PASS',provenance:'PASS',repeatability:'PASS'};
function input(id,configuration,environment,gates=pass,extra={}){return{id,configuration,environment,evidence:'external-assessed mock evidence',gates,...extra}}
assert.equal(t.submit(input('KR84-SEALED','Kr-84 gas','sealed-container')).status,'PROMOTE');
assert.equal(t.transfer('KR84-SEALED','open-atmosphere').authorized,false);
assert.equal(t.current('Kr-84 gas','open-atmosphere').status,'UNTESTED');
assert.equal(t.submit(input('KR84-OPEN-UNKNOWN','Kr-84 gas','open-atmosphere',{...pass,environment:'UNKNOWN'},{origin:'KR84-SEALED',parentAccepted:'KR84-SEALED'})).status,'HOLD');
assert.equal(t.current('Kr-84 gas','open-atmosphere').status,'HOLD');
assert.equal(t.submit(input('KR84-OPEN-FAIL','Kr-84 gas','open-atmosphere',{...pass,environment:'FAIL'},{origin:'KR84-OPEN-UNKNOWN'})).status,'REJECT');
assert.equal(t.current('Kr-84 gas','open-atmosphere').status,'REJECT');
assert.equal(t.submit(input('KR84-OPEN-PASS','Kr-84 gas','open-atmosphere',pass,{origin:'KR84-OPEN-FAIL',parentAccepted:'KR84-SEALED'})).status,'PROMOTE');
assert.equal(t.current('Kr-84 gas','open-atmosphere').authorized,true);
assert.equal(t.submit(input('KR84-OPEN-RETEST','Kr-84 gas','open-atmosphere',{...pass,repeatability:'UNKNOWN'},{origin:'KR84-OPEN-PASS'})).status,'HOLD');
assert.equal(t.current('Kr-84 gas','open-atmosphere').authorized,false);
assert.equal(t.current('Kr-84 gas','sealed-container').authorized,true);
assert.throws(()=>t.submit(input('INVALID-PARENT','Kr-84 gas','new',{...pass},{parentAccepted:'KR84-OPEN-FAIL'})),/Parent not accepted/);
assert.throws(()=>t.submit(input('BAD-CONFIG','Kr-85 gas','new',pass,{parentAccepted:'KR84-SEALED'})),/same configuration/);
assert.throws(()=>t.submit(input('KR84-SEALED','Kr-84 gas','new')),/Immutable ID/);
assert.deepEqual(t.verify(),{observations:5,promoted:2,held:2,rejected:1,appendOnly:true,verified:true});
assert.equal(t.journal[1].result.status,'HOLD');
assert.ok(Object.isFrozen(t.journal[1].candidate.gates));
console.log('PASS B133: environment transfer never inherits approval; five immutable observations; newest trial controls current authorization');
