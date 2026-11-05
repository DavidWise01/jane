'use strict';
const assert=require('node:assert/strict');
const m=require('./jane-b155-isa.cjs');
const d=m.assemble();assert.equal(d.length,366);assert.equal(m.assertComposition(d).status,'PASS');
for(const [r,s] of [['a',1],['b',123],['c',245]]){assert.equal(m.address(r,1).global,s);assert.equal(m.address(r,122).global,s+121)}
for(const g of [1,62,63,122,123,184,185,244,245,306,307,366]){const x=m.decode(g);assert.equal(x.global,g);assert.equal(m.address(x.register,x.local).global,g)}
assert.equal(d.filter(x=>x.kind==='Box62').length,186);assert.equal(d.filter(x=>x.kind==='Toroid60').length,180);
assert.equal(new Set(d.map(x=>x.global)).size,366);assert.equal(m.address('c',62).global,306);assert.equal(m.address('c',63).global,307);
assert.throws(()=>m.decode(367),/INVALID/);assert.throws(()=>m.address('d',1),/INVALID/);
const machine=new m.Machine();
assert.equal(machine.execute('ASSEMBLE').length,366);
assert.equal(machine.execute('READ',{register:'a',local:62}).kind,'Box62');
assert.equal(machine.execute('READ',{register:'a',local:63}).kind,'Toroid60');
assert.equal(machine.execute('STEP',{register:'a',sign:'-'}).local,122);
assert.equal(machine.execute('STEP',{register:'a',sign:'+'}).local,1);
assert.equal(machine.execute('STEP',{register:'b',sign:'+'}).global,124);
assert.equal(machine.execute('WITNESS',{register:'c'}).witness,'c1');
assert.equal(machine.execute('CHECK').status,'PASS');
assert.equal(machine.execute('STEP',{register:'d',sign:'+'}).status,'HOLD');
assert.equal(machine.execute('FOO').status,'HOLD');
assert.equal(machine.replayAudit().status,'PASS');
machine.journal[0].result.length=365;assert.equal(machine.replayAudit().status,'HOLD');
const altered=d.slice();altered[1]={...altered[1],global:3};assert.equal(m.assertComposition(altered).status,'HOLD');
console.log('PASS B155: three 122 registers compose exactly 366 derived addresses; ISA address/read/step/assemble/witness/check; hash-chain integrity; no independent d allocation');
