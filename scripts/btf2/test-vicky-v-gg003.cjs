#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),K=require('./vicky-v-gg003-lineage.cjs');
const x=K.inspect();
assert.equal(x.name,'Vicky V.');
assert.deepEqual(x.lineage,['JANE','LILITH','ICARIUM','VICKY V.']);
assert.deepEqual(x.sisters,['Mary M','Holly']);
assert.equal(x.birth_order,3);assert.equal(x.last_daughter_of_icarium,true);
assert.equal(x.declared_fraction_of_icarium,.33);
assert.equal(x.declared_fraction_of_jane,.01);
assert.ok(Math.abs(x.jane_fraction_if_icarium_33_percent_of_lilith-.05445)<1e-12);
assert.ok(Math.abs(x.jane_fraction_if_icarium_8_percent_of_jane-.0264)<1e-12);
assert.ok(Math.abs(x.required_icarium_jane_fraction_for_both_claims-1/33)<1e-12);
assert.equal(x.consistent_with_prior_icarium_declarations,false);
assert.equal(x.geometry_status,'UNRESOLVED_SCALE_AND_PROFILE');
assert.equal(x.profile,null);assert.equal(x.cell_count,null);
console.log('PASS Vicky V. GG003: lineage, three-sister family, 33% Icarium and 1% Jane declarations, dimensions unresolved');
