'use strict';
const assert=require('node:assert/strict');
const m=require('./jane-b154-closed-loop.cjs');
for(const [i,brace]of ['H','O','N'].entries()){
 const x=m.roundTrip(brace);assert.equal(x.status,'PASS');
 assert.equal(x.forward.records.length,122);assert.equal(x.reverse.records.length,122);
 assert.equal(x.invariants.forward.boxEntries,62);assert.equal(x.invariants.forward.toroidEntries,60);
 assert.equal(x.invariants.reverse.boxEntries,62);assert.equal(x.invariants.reverse.toroidEntries,60);
 assert.equal(x.invariants.mirror,true);assert.equal(x.invariants.steps,244);
 assert.equal(x.forward.records.find(e=>e.from===62).to,63);
 assert.equal(x.forward.records.at(-1).to,1);
 assert.equal(x.reverse.records[0].to,122);
 assert.equal(x.reverse.records.find(e=>e.from===63).to,62);
 const altered=JSON.parse(JSON.stringify(x.forward));altered.records[50].to=100;assert.equal(m.audit(altered).status,'HOLD');
 const missing=JSON.parse(JSON.stringify(x.forward));missing.records.pop();assert.equal(m.audit(missing).status,'HOLD');
 const reordered=JSON.parse(JSON.stringify(x.forward));[reordered.records[1],reordered.records[2]]=[reordered.records[2],reordered.records[1]];assert.equal(m.audit(reordered).status,'HOLD');
 assert.equal(x.forward.records[0].witness,['a1','b1','c1'][i]);
}
assert.equal(m.all().reduce((a,x)=>a+x.forward.records.length+x.reverse.records.length,0),732);
for(const s of [2,62,63,122])assert.equal(m.roundTrip('H',s).status,'PASS');
assert.throws(()=>m.walk('H','*'),/INVALID_WALK/);
console.log('PASS B154: three independent 122+122 exact reverse closed loops, 732 signed steps, 62/60 coverage, seam, tamper, no quorum');
