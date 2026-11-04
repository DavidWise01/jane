'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pair,validate}=require('./jane-b147-1-shadow-base.cjs');
const config=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../b147/shadow-base-v1.json'),'utf8'));
assert.equal(validate(config).status,'SYMBOLIC_PASS');
const p=pair();assert.equal(p.display,'+1+1');
assert.equal(p.primary.effective+p.shadow.effective,0);
assert.equal(1+1,2);
for(const change of [
 d=>d.notation.base=10,d=>d.notation.alternative='-+4',
 d=>d.notation.shadowEffective=1,d=>d.notation.projected=2,
 d=>d.positions.reverse(),d=>d.scope='PHYSICS_PROVEN'
]){const d=JSON.parse(JSON.stringify(config));change(d);assert.equal(validate(d).status,'HOLD');}
assert.throws(()=>pair(1,-1),/EXPECTED_TWO_POSITIVE_DISPLAY_TOKENS/);
console.log('PASS B147.1: base 11 / -+5 notation, five referents, display +1+1 -> 0 shadow projection, six negative controls');
