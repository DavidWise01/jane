#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),m=require('./jane-b122-one-codon.cjs');
const a=m.audit(),slots=m.codon();
assert.equal(a.name,'ONE CODON');assert.equal(a.cubit_count,2);assert.equal(a.lineage_slots,16);assert.equal(a.choice_pool,20);
assert.equal(slots.length,16);assert.equal(new Set(slots.map(s=>s.address)).size,16);
assert.equal(slots[0].address,'CODON001:CU0:000');assert.equal(slots[15].address,'CODON001:CU1:111');
const swapped=m.codon(m.candidates.slice(0,15).map(s=>s.choice_id).concat('C16'));
assert.equal(swapped[15].status,'unassigned');
assert.throws(()=>m.codon(m.candidates.slice(1,17).map(s=>s.choice_id)),/foundation/);
assert.throws(()=>m.codon(Array(16).fill('C00')),/distinct/);
console.log('PASS B122: ONE CODON, 2 analytical cubits, 16 slots from 20 candidates, 11 frozen foundation members');
