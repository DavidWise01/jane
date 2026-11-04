'use strict';
const crypto=require('node:crypto');
const SLOT_IDS=Object.freeze(['S1','S2','S3','S4','S5']);
function digest(value){return crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex')}
function validNumber(n){return typeof n==='number'&&Number.isFinite(n)}
function grade(o){
 const requirements=['eventId','slot','witness','timestamp','frame','source','direction','before','after','threshold','uncertainty'];
 if(!o||requirements.some(k=>o[k]===null||o[k]===undefined||o[k]===''))return{status:'HOLD',reason:'MISSING_EVIDENCE_FIELD',physicalPromotion:false};
 if(!SLOT_IDS.includes(o.slot)||!['IN','OUT'].includes(o.direction)||!['a1','b1','c1'].includes(o.witness))return{status:'HOLD',reason:'INVALID_SLOT_DIRECTION_OR_WITNESS',physicalPromotion:false};
 if(![o.before,o.after,o.threshold,o.uncertainty].every(validNumber)||o.uncertainty<0)return{status:'HOLD',reason:'INVALID_NUMERIC_MEASUREMENT',physicalPromotion:false};
 if(!Number.isFinite(Date.parse(o.timestamp)))return{status:'HOLD',reason:'INVALID_TIME',physicalPromotion:false};
 const inward=o.direction==='IN';
 const clear=inward?(o.before-o.uncertainty>o.threshold&&o.after+o.uncertainty<o.threshold):(o.before+o.uncertainty<o.threshold&&o.after-o.uncertainty>o.threshold);
 if(!clear)return{status:'HOLD',reason:'UNCERTAINTY_OVERLAPS_BOUNDARY_OR_WRONG_DIRECTION',physicalPromotion:false};
 if(o.provenanceKind==='SIMULATION'&&o.frame==='B150_VISUAL_UNITS'&&o.source==='B150_PIXEL_SCOUT')return{status:'SIMULATED_CROSSING',reason:'SYNTHETIC_BOUNDARY_CONFIRMED',physicalPromotion:false};
 return{status:'HOLD',reason:'PHYSICAL_PROVENANCE_NOT_ATTESTED',physicalPromotion:false};
}
class Journal{
 constructor(){this.entries=[]}
 append(o){if(!o||!o.eventId||this.entries.some(e=>e.observation.eventId===o.eventId))throw Error('DUPLICATE_OR_MISSING_EVENT_ID');
 const verdict=grade(o),payload={seq:this.entries.length+1,previous:this.entries.at(-1)?.hash||'GENESIS',observation:JSON.parse(JSON.stringify(o)),verdict},entry=Object.freeze({...payload,hash:digest(payload)});
 this.entries.push(entry);return entry}
 replay(){let prev='GENESIS';const out=[];for(let i=0;i<this.entries.length;i++){
 const entry=this.entries[i],{hash,...payload}=entry;
 if(entry.seq!==i+1||entry.previous!==prev||digest(payload)!==hash||JSON.stringify(grade(entry.observation))!==JSON.stringify(entry.verdict))throw Error('JOURNAL_INTEGRITY_FAILURE');
 prev=hash;out.push({seq:entry.seq,id:entry.observation.eventId,status:entry.verdict.status});
 }return{status:'REPLAY_PASS',count:out.length,physicalPromotions:0,quorum:false,records:out}}
}
module.exports={SLOT_IDS,grade,Journal};
