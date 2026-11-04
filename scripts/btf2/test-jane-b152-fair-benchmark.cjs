'use strict';
const assert=require('node:assert/strict');
const {SCENARIO,run,verify,outcome,compare}=require('./jane-b152-fair-benchmark.cjs');
const {WITNESSES}=require('./jane-b151-scout-exploration.cjs');
assert.equal(outcome('S3',1),'HOLD');assert.equal(outcome('S3',2),'HOLD');assert.equal(outcome('S3',3),'SIMULATED_CROSSING');
assert.equal(outcome('S5',1),'HOLD');assert.equal(outcome('S5',2),'SIMULATED_CROSSING');
for(const w of WITNESSES)for(const s of ['MEMORY','ROUND_ROBIN']){
 const a=run(s,w);assert.equal(a.trace.length,SCENARIO.steps);assert.equal(verify(a).status,'PASS');
 assert.deepEqual(a,run(s,w));
 const hacked=JSON.parse(JSON.stringify(a));hacked.trace[0].observation.status='PHYSICS_PASS';assert.equal(verify(hacked).status,'HOLD');
 const reorder=JSON.parse(JSON.stringify(a));reorder.trace.reverse();assert.equal(verify(reorder).status,'HOLD');
}
const c=compare();assert.equal(c.physicalPromotion,false);assert.equal(c.quorum,false);
assert.equal(c.memory.visits,3*SCENARIO.steps);assert.equal(c.roundRobin.visits,3*SCENARIO.steps);
assert.deepEqual(compare(),c);
assert.throws(()=>run('VOTING','a1'),/UNKNOWN/);assert.throws(()=>outcome('S6',1),/INVALID/);

assert.equal(c.memory.travelVisualUnits,415);
assert.equal(c.roundRobin.travelVisualUnits,566);
assert.equal(c.memory.uncertaintiesResolved,6);
assert.equal(c.roundRobin.uncertaintiesResolved,5);
assert.equal(c.verdict,'MEMORY_PARETO_DOMINATES');
const stress=compare({...SCENARIO,id:'ALL_HOLD',holdsBeforeClear:[20,20,20,20,20]});
assert.equal(stress.verdict,'TRADEOFF_NO_UNQUALIFIED_WINNER');
assert.ok(stress.memory.coverage<stress.roundRobin.coverage);
assert.ok(stress.memory.repeatedHolds>stress.roundRobin.repeatedHolds);

console.log('PASS B152 deterministic benchmark, equal visit budgets, three independent witnesses, tamper detection, no preselected winner');
console.log(JSON.stringify({memory:c.memory,roundRobin:c.roundRobin,verdict:c.verdict,wins:c.wins,losses:c.losses}));
