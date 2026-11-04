#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),{Trainer,evaluate}=require('./jane-b129-generational-trainer.cjs');
const t=new Trainer();
const pass={id:'hydrogen-reference-1',gates:{conservation:true,stability:true,provenance:true,repeatability:true}};
assert.equal(t.submit(pass).decision,'PROMOTE');
const fail={id:'unbound-intermediate-1',gates:{conservation:true,stability:false,provenance:true,repeatability:true}};
assert.equal(t.submit(fail).decision,'RETAIN_FAILURE_ONLY');
assert.equal(t.genePool.length,1);
assert.equal(t.events.length,2);
assert.equal(t.events[1].result.failed[0],'stability');
assert.deepEqual(t.audit(),{observations:2,promoted:1,rejected:1,failed_in_active_pool:0,verified:true});
assert.equal(evaluate({id:'incomplete',gates:{stability:true}}).promote,false);
assert.throws(()=>t.submit(pass),/Duplicate/);
console.log('PASS B129: failure witnessed and preserved, never promoted; complete gates required');
