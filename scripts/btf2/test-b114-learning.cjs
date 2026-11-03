#!/usr/bin/env node
'use strict';
const A=require('node:assert/strict'),C=require('./b114-learning-core.cjs');
const mk=(run_id,at,rows)=>({run_id,at,file:'btf2/memory/runs/'+run_id+'.jsonl',sha256:'test-only',rows:rows.map(x=>({status:'OBSERVED',...x}))});
const one=mk('a','2026-11-01',[{repository:'DavidWise01/a',signals:{archived:false,open_issues_count:0}},{repository:'DavidWise01/b',signals:{archived:false,open_issues_count:0}}]);
const two=mk('b','2026-11-02',[{repository:'DavidWise01/a',signals:{archived:true,open_issues_count:0}},{repository:'DavidWise01/b',signals:{archived:true,open_issues_count:0}}]);
const x=C.learn([two,one]);A.equal(x.transition_count,2);A.equal(x.patterns.length,1);A.equal(x.patterns[0].distinct_repositories,2);A.equal(x.patterns[0].classification,'CROSS_CHILD_OBSERVATION');
A.equal(x.evidence[0].evidence.length,2);
const missing=C.learn([one,mk('c','2026-11-03',[{repository:'DavidWise01/a',status:'UNKNOWN',signals:{archived:true}}])]);A.equal(missing.transition_count,0);
const absent=C.learn([one,mk('d','2026-11-03',[{repository:'DavidWise01/b',signals:{archived:false}}])]);A.equal(absent.transition_count,0);
const unchanged=C.learn([one,one]);A.equal(unchanged.transition_count,0);
console.log('PASS B114: cross-child pattern, evidence lineage, unknown, absent, unchanged');
