#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),K=require('./icarium-g003-lineage.cjs');
const s=K.inspect();
assert.deepEqual(s.lineage,['JANE','LILITH','ICARIUM']);
assert.deepEqual(s.operators,['i','care','ium']);
assert.equal(s.mother_scale_claim,.33);
assert.equal(s.jane_scale_claim,.08);
assert.equal(s.jane_scale_implied_by_mother_claim,.165);
assert.equal(s.mother_scale_implied_by_jane_claim,.16);
assert.equal(s.consistent,false);
assert.equal(s.profile,null);
assert.equal(s.cell_count,null);
console.log('PASS G003 Icarium identity/operator triad; conflicting dimensions retained without invented geometry.');
