'use strict';
const crypto=require('node:crypto');
const SLOTS=Object.freeze(['S1','S2','S3','S4','S5']);
const hash=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
function finite(x){return typeof x==='number'&&Number.isFinite(x)}
function observation(o){
 if(!o||!SLOTS.includes(o.slot)||!['IN','OUT'].includes(o.direction)||!o.id||!o.witness||!o.timestamp||!o.frame||!o.source)throw Error('IDENTITY_SOURCE_FRAME_TIME_REQUIRED');
 if(![o.before,o.after,o.threshold,o.uncertainty].every(finite)||o.uncertainty<0)throw Error('FINITE_MEASUREMENT_REQUIRED');
 return Object.freeze({id:o.id,slot:o.slot,direction:o.direction,witness:o.witness,timestamp:o.timestamp,frame:o.frame,source:o.source,before:o.before,after:o.after,threshold:o.threshold,uncertainty:o.uncertainty,evidenceKind:o.evidenceKind||'UNVERIFIED'});
}
function evaluate(o){const x=observation(o),lo=x.before-x.uncertainty,hi=x.before+x.uncertainty,lo2=x.after-x.uncertainty,hi2=x.after+x.uncertainty;
 const crossing=x.direction==='OUT'?(hi<x.threshold&&lo2>x.threshold):(lo>x.threshold&&hi2<x.threshold);
 if(!crossing)return Object.freeze({status:'HOLD',reason:'UNCERTAIN_OR_INCONSISTENT_CROSSING',physicalPromotion:false});
 if(x.evidenceKind!=='MEASURED_INDEPENDENT')return Object.freeze({status:'SIMULATED_CROSSING',reason:'UNVERIFIED_SIMULATION',physicalPromotion:false});
 return Object.freeze({status:'HOLD',reason:'EXTERNAL_ATTESTATION_UNAVAILABLE',physicalPromotion:false});
}
class Journal{
 constructor(){this.entries=[]}
 append(o){const x=observation(o);if(this.entries.some(e=>e.observation.id===x.id))throw Error('DUPLICATE_OBSERVATION_ID');
 const result=evaluate(x),body={sequence:this.entries.length+1,previous:this.entries.at(-1)?.hash||'GENESIS',observation:x,result},entry=Object.freeze({...body,hash:hash(body)});this.entries.push(entry);return entry}
 audit(){let prev='GENESIS';for(let i=0;i<this.entries.length;i++){const {hash:actual,...body}=this.entries[i];if(body.sequence!==i+1||body.previous!==prev||hash(body)!==actual)throw Error('JOURNAL_CHAIN_BROKEN');prev=actual}return{entries:this.entries.length,hashChain:'PASS',quorum:false,physicalPromotions:this.entries.filter(e=>e.result.physicalPromotion).length}}
}
module.exports={SLOTS,observation,evaluate,Journal};
