'use strict';
const crypto=require('node:crypto');
const {plan,SLOTS,WITNESSES,RADII}=require('./jane-b151-scout-exploration.cjs');
const sha=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const SCENARIO=Object.freeze({id:'B152-SYNTHETIC-V1',steps:12,starts:[5,27,53],holdsBeforeClear:[0,0,2,0,1],status:'SIMULATED_ONLY'});
function outcome(slot,attempt,scenario=SCENARIO){
 const idx=SLOTS.indexOf(slot);
 if(idx<0||!Number.isInteger(attempt)||attempt<1)throw Error('INVALID_SLOT_OR_ATTEMPT');
 return attempt<=scenario.holdsBeforeClear[idx]?'HOLD':'SIMULATED_CROSSING';
}
function run(strategy,witness,scenario=SCENARIO){
 if(!['MEMORY','ROUND_ROBIN'].includes(strategy)||!WITNESSES.includes(witness))throw Error('UNKNOWN_STRATEGY_OR_WITNESS');
 const widx=WITNESSES.indexOf(witness),trace=[],visits=[0,0,0,0,0],counts=[0,0,0,0,0],resolved=new Set(),held=new Set();
 let radius=scenario.starts[widx],travel=0,previous=null,head='GENESIS',repeatedHolds=0;
 for(let t=0;t<scenario.steps;t++){
  const choice=strategy==='MEMORY'
   ?plan(trace.map(q=>q.observation),{witness,radius,previousSlot:previous}).targetSlot
   :SLOTS[(widx+t)%SLOTS.length];
  const i=SLOTS.indexOf(choice),before=radius,next=RADII[i],distance=Math.abs(before-next);
  radius=next;travel+=distance;visits[i]++;counts[i]++;
  const status=outcome(choice,counts[i],scenario);
  if(status==='HOLD'){if(held.has(choice))repeatedHolds++;held.add(choice)}
  else if(held.has(choice))resolved.add(choice);
  const observation={witness,slot:choice,status,source:'B150_PIXEL_SCOUT',frame:'B150_VISUAL_UNITS',physicalPromotion:false};
  const payload={step:t+1,previous:head,observation,radiusBefore:before,radiusAfter:next,distance,decision:strategy,simulated:true};
  const entry={...payload,hash:sha(payload)};trace.push(entry);head=entry.hash;previous=choice;
 }
 const metrics={visits:trace.length,coverage:visits.filter(Boolean).length,uncertaintiesResolved:resolved.size,remainingUnresolved:[...held].filter(s=>!resolved.has(s)).length,repeatedHolds,travelVisualUnits:Number(travel.toFixed(6)),holds:trace.filter(x=>x.observation.status==='HOLD').length};
 return{strategy,witness,scenarioId:scenario.id,metrics,trace,head,physicalPromotion:false};
}
function verify(r,scenario=SCENARIO){
 if(!r||r.scenarioId!==scenario.id||!['MEMORY','ROUND_ROBIN'].includes(r.strategy)||!WITNESSES.includes(r.witness)||!Array.isArray(r.trace))return{status:'HOLD',reason:'INVALID_RUN'};
 let prev='GENESIS';
 for(let i=0;i<r.trace.length;i++){
  const e=r.trace[i],{hash,...payload}=e;
  if(payload.step!==i+1||payload.previous!==prev||sha(payload)!==hash||payload.observation?.physicalPromotion!==false)return{status:'HOLD',reason:'TAMPER_OR_REORDER'};
  prev=hash;
 }
 const clean=run(r.strategy,r.witness,scenario);
 if(JSON.stringify(clean)!==JSON.stringify(r))return{status:'HOLD',reason:'REPLAY_MISMATCH'};
 return{status:'PASS',count:r.trace.length,quorum:false,physicalPromotion:false};
}
function aggregate(runs){
 const out={coverage:0,uncertaintiesResolved:0,remainingUnresolved:0,repeatedHolds:0,travelVisualUnits:0,holds:0,visits:0};
 for(const run of runs)for(const key of Object.keys(out))out[key]+=run.metrics[key];
 out.travelVisualUnits=Number(out.travelVisualUnits.toFixed(6));
 return out;
}
function compare(scenario=SCENARIO){
 const memory=WITNESSES.map(w=>run('MEMORY',w,scenario)),baseline=WITNESSES.map(w=>run('ROUND_ROBIN',w,scenario));
 const a=aggregate(memory),b=aggregate(baseline);
 const objectives=[
 ['coverage',true],['uncertaintiesResolved',true],['remainingUnresolved',false],['repeatedHolds',false],['travelVisualUnits',false]
 ];
 const wins=objectives.filter(([k,high])=>high?a[k]>b[k]:a[k]<b[k]).map(([k])=>k);
 const losses=objectives.filter(([k,high])=>high?a[k]<b[k]:a[k]>b[k]).map(([k])=>k);
 const verdict=losses.length===0&&wins.length>0?'MEMORY_PARETO_DOMINATES':wins.length===0&&losses.length>0?'ROUND_ROBIN_PARETO_DOMINATES':wins.length===0&&losses.length===0?'TIE':'TRADEOFF_NO_UNQUALIFIED_WINNER';
 return{schema:'JANE-B152-FAIR-EXPLORATION-BENCHMARK-v1',scenario,stepBudgetPerWitness:scenario.steps,memory:a,roundRobin:b,wins,losses,verdict,comparators:{coverage:'MAX',uncertaintiesResolved:'MAX',remainingUnresolved:'MIN',repeatedHolds:'MIN',travelVisualUnits:'MIN'},hashHeads:{memory:memory.map(r=>r.head),roundRobin:baseline.map(r=>r.head)},physicalPromotion:false,independentWitnesses:3,quorum:false};
}
module.exports={SCENARIO,outcome,run,verify,aggregate,compare};
