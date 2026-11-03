#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),K=require('./mary-m-gg001-lineage.cjs');
const x=K.inspect();
assert.equal(x.name,'Mary M');
assert.deepEqual(x.lineage,['JANE','LILITH','ICARIUM','MARY M']);
assert.equal(x.declared_mary_fraction_of_icarium,.67);
assert.equal(x.declared_mary_fraction_of_jane,.04);
assert.ok(Math.abs(x.jane_fraction_if_icarium_is_33_percent_lilith-.11055)<1e-14);
assert.ok(Math.abs(x.jane_fraction_if_icarium_is_8_percent_jane-.0536)<1e-14);
assert.ok(Math.abs(x.icarium_jane_fraction_required_for_exact_4_percent_mary-4/67)<1e-14);
assert.equal(x.consistent_with_33_percent_icarium_lilith,false);
assert.equal(x.consistent_with_8_percent_icarium_jane,false);
assert.equal(x.profile,null);
console.log('PASS Mary M GG001: lineage, all source declarations, explicit arithmetic discrepancies, no invented geometry');
