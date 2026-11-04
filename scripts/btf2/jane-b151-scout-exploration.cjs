'use strict';
const crypto=require('node:crypto');
const SLOTS=Object.freeze(['S1','S2','S3','S4','S5']);
const WITNESSES=Object.freeze(['a1','b1','c1']);
const RADII=Object.freeze([20,30,40,51,62]);
const sha=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const goodEvent=e=>!!e&&SLOTS.includes(e.slot)&&WITNESSES.includes(e.witness)&&['SIMULATED_CROSSING','HOLD'].includes(e.status)&&e.physicalPromotion===false&&e.source==='B150_PIXEL_SCOUT'&&e.frame==='B150_VISUAL_UNITS';
function historyFor(entries,witness){
 if(!WITNESSES.includes(witness))throw Error('UNKNOWN_WITNESS');
 if(!Array.isArray(entries))throw Error('HISTORY_ARRAY_REQUIRED');
 const h=SLOTS.map(slot=>({slot,visits:0,holds:0,clear:0}));
 for(const raw of entries){const e=raw?.obs||raw;if(!goodEvent(e))continue;if(e.witness!==witness)continue;const i=SLOTS.indexOf(e.slot);h[i].visits++;if(e.status==='HOLD')h[i].holds++;else h[i].clear++;}
 return h;
}
function plan(entries,{witness,radius,previousSlot=null}={}){
 if(!WITNESSES.includes(witness)||!Number.isFinite(radius)||radius<0||radius>70)throw Error('WITNESS_OR_POSITION_INVALID');
 const states=historyFor(entries,witness);
 const scores=states.map((s,i)=>({
  slot:s.slot,radius:RADII[i],
  visits:s.visits,holds:s.holds,clear:s.clear,
  score:100-25*s.visits+35*s.holds-0.1*Math.abs(radius-RADII[i])-(previousSlot===s.slot?5:0)
 }));
 scores.sort((a,b)=>b.score-a.score||SLOTS.indexOf(a.slot)-SLOTS.indexOf(b.slot));
 const choice=scores[0];
 return{witness,targetSlot:choice.slot,targetRadius:choice.radius,score:choice.score,reason:choice.visits===0?'UNVISITED':choice.holds>0?'REVISIT_UNCERTAIN':'LOWEST_COVERAGE',basis:'OWN_WITNESS_OBSERVATIONS_ONLY',physicalPromotion:false,scores};
}
class Decisions{
 constructor(){this.entries=[]}
 append(choice){
  if(!WITNESSES.includes(choice?.witness)||!SLOTS.includes(choice.targetSlot)||choice.physicalPromotion!==false||choice.basis!=='OWN_WITNESS_OBSERVATIONS_ONLY')throw Error('INVALID_PLAN');
  const payload={sequence:this.entries.length+1,previous:this.entries.at(-1)?.hash||'GENESIS',choice:JSON.parse(JSON.stringify(choice))},entry=Object.freeze({...payload,hash:sha(payload)});
  this.entries.push(entry);return entry;
 }
 replay(){let previous='GENESIS';for(let i=0;i<this.entries.length;i++){const {hash,...payload}=this.entries[i];if(payload.sequence!==i+1||payload.previous!==previous||sha(payload)!==hash)throw Error('PLAN_CHAIN_INVALID');previous=hash;}return{status:'PASS',count:this.entries.length,quorum:false,physicalPromotions:0}}
}
module.exports={SLOTS,WITNESSES,RADII,historyFor,plan,Decisions};
