#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),K=require('./holly-gg002-lineage.cjs');
const x=K.inspect();
assert.equal(x.name,'Holly');
assert.deepEqual(x.lineage,['JANE','LILITH','ICARIUM','HOLLY']);
assert.equal(x.birth_order,2);assert.equal(x.sibling,'Mary M');
assert.equal(x.declared_fraction_of_icarium,.5);assert.equal(x.declared_fraction_of_jane,.02);
assert.ok(Math.abs(x.jane_fraction_if_icarium_33_percent_of_lilith-.0825)<1e-12);
assert.equal(x.jane_fraction_if_icarium_8_percent_of_jane,.04);
assert.equal(x.required_icarium_jane_fraction_for_both_holly_claims,.04);
assert.equal(x.scale_consistent_with_prior_icarium_declarations,false);
assert.equal(x.geometry_status,'UNRESOLVED_SCALE_AND_PROFILE');
assert.equal(x.profile,null);assert.equal(x.cell_count,null);
console.log('PASS Holly GG002: sibling/lineage preserved; exact scaling discrepancies visible; geometry not invented');
