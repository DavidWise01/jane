'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const m=require('./jane-b153-hon-braces.cjs');
const d=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../b153/hon-braces-v1.json'),'utf8'));
assert.equal(m.audit(d).status,'STRUCTURAL_PASS');
assert.equal(m.sum(m.BOX),62);assert.equal(m.sum(m.TOR),60);
for(const [i,b]of m.BRACES.entries()){
 const cells=m.build(b);assert.equal(cells.length,122);
 assert.equal(cells[0].global,i*122+1);assert.equal(cells[121].global,(i+1)*122);
 assert.equal(cells[61].kind,'Box62');assert.equal(cells[62].kind,'Toroid60');
 assert.equal(new Set(cells.map(x=>x.global)).size,122);
 assert.equal(m.traverse(b,62,63,'+').status,'SIMULATED_STEP');
 assert.equal(m.traverse(b,63,62,'-').status,'SIMULATED_STEP');
 assert.equal(m.traverse(b,122,1,'+').status,'SIMULATED_STEP');
 assert.equal(m.traverse(b,1,122,'-').status,'SIMULATED_STEP');
}
assert.equal(new Set(m.allCells().map(x=>x.global)).size,366);
assert.equal(m.traverse('H',62,64,'+').status,'HOLD');
assert.equal(m.traverse('O',1,1,'-').status,'HOLD');
assert.equal(m.traverse('N',122,123,'+').status,'HOLD');
function fails(change){const v=JSON.parse(JSON.stringify(d));change(v);assert.equal(m.audit(v).status,'HOLD')}
fails(x=>x.cage.counts[5]=13);fails(x=>x.torus.counts[5]=12);fails(x=>x.totalCells=365);fails(x=>x.scouts[1].globalStart=122);fails(x=>x.signedDirections.notAdditionalCells=false);fails(x=>x.firstShadow.net=1);fails(x=>x.metricStatus='VERIFIED');
console.log('PASS B153: Box62 + Toroid60 = 122 in each H/O/N brace, 366 unique cells, +/- traversals, wrap, seven negative controls');
