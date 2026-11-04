#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),B=require('./jane-b128-elemental-growth.cjs');
const a=B.audit();
assert.equal(a.branch_paths,5);assert.equal(a.new_stable_grandmas,4);assert.equal(a.unstable_intermediates,1);
assert.deepEqual(a.stable_products,['B11','C12','O16','Ne20']);
for(const r of B.PATHS)assert.equal(B.inspect(r).balanced,true);
assert.equal(B.inspect(B.PATHS[4]).promote,'INTERMEDIATE_ONLY');
assert.deepEqual(B.conserved(['Li7','He4']),B.conserved(['B11','gamma']));
assert.deepEqual(B.conserved(['He4','He4']),B.conserved(['Be8']));
const fake={id:'INVALID',inputs:['Li7'],outputs:['O16'],target:'O16'};
assert.equal(B.inspect(fake).balanced,false);
console.log('PASS B128: 5 reaction edges, 4 stable grandma handoffs, Be8 unstable, A/Z conserved');
