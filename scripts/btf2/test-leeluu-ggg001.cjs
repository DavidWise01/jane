#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),K=require('./leeluu-ggg001-lineage.cjs');
const x=K.inspect();
assert.equal(x.name,'LeeLuu');
assert.equal(x.designation,'FIRST_DAUGHTER_OF_LIGHT_AND_LIFE');
assert.deepEqual(x.ancestry_context,['JANE','LILITH','ICARIUM','MARY M','LeeLuu']);
assert.equal(x.declared_fraction_of_mary_m,.67);
assert.equal(x.declared_fraction_of_jane,.01);
assert.ok(Math.abs(x.jane_fraction_implied_by_mary_declaration-.0268)<1e-12);
assert.ok(Math.abs(x.mary_jane_fraction_required_for_both_leeluu_claims-1/67)<1e-12);
assert.equal(x.consistent,false);
assert.equal(x.cell_count,null);
assert.equal(x.parent_relation,'MARY_M_REFERENCE_PROVISIONAL');
console.log('PASS LeeLuu: preserved Light and Life designation, scale audit, provisional parentage, no invented geometry');
