'use strict';
const assert=require('node:assert/strict'),m=require('./jane-b157-pre-isa-boundary.cjs');
const s=m.sources(),d=m.assemble(s);
assert.equal(m.audit(s).status,'STRUCTURAL_PASS');
assert.equal(d.length,366);assert.equal(new Set(d.map(x=>x.global)).size,366);
for(const [r,first] of [['a',1],['b',123],['c',245]]){assert.equal(s[r].length,122);assert.equal(m.address(r,1).global,first);assert.equal(m.address(r,122).global,first+121);assert.equal(s[r].filter(x=>x.kind==='Box62').length,62);assert.equal(s[r].filter(x=>x.kind==='Toroid60').length,60);}
assert.equal(m.decode(366).register,'c');assert.equal(m.decode(123).local,1);assert.equal(m.decode(0),null);assert.equal(m.address('d',1),null);
assert.equal(m.observe('a',62).cell.kind,'Box62');assert.equal(m.observe('a',63).cell.kind,'Toroid60');
assert.equal(m.next('a',122,'+').to.local,1);assert.equal(m.next('b',1,'-').to.local,122);
assert.equal(m.next('a',62,'?').status,'HOLD');
const bad=m.sources();bad.c[40]={...bad.c[40],global:300};assert.equal(m.audit(bad).status,'HOLD');
const missing=m.sources();missing.b.pop();assert.equal(m.audit(missing).status,'HOLD');
assert.equal(m.audit().isaDefined,false);
console.log('PASS B157 PRE-ISA: 3x122 = 366 derived addresses, 62/60 layers, H/O/N witnesses, +/- addresses, no defined ISA');
