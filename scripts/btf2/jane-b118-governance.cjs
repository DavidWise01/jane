'use strict';
// JANE B118: deterministic governance simulation. No external actions, voting, or quorum.
const crypto=require('node:crypto');
const STATUS=Object.freeze({YES:'YES',HOLD:'HOLD',NO:'NO'});
const RISK_REASONS=Object.freeze(['coercion','privacy_violation','ownership_override','destructive_change']);
function normalize(o){
 if(!o||typeof o!=='object')throw Error('Observation required');
 const witness=String(o.witness||'').trim(),source=String(o.source||'').trim(),claim=String(o.claim||'').trim();
 const evidence=String(o.evidence||'').trim(),event_time=String(o.event_time||'').trim();
 const risk=String(o.risk||'none').trim(),uncertainty=String(o.uncertainty||'unknown').trim();
 if(!witness||!claim)throw Error('Witness and claim required');
 if(risk!=='none'&&!RISK_REASONS.includes(risk))throw Error('Unknown risk type');
 return Object.freeze({witness,source,claim,evidence,event_time,risk,uncertainty});
}
function gate(observation,prior=[]){
 const o=normalize(observation);
 const conflict=prior.some(p=>p.claim!==o.claim&&p.source&&p.source===o.source);
 if(o.risk!=='none')return {decision:STATUS.NO,reason:'BOUNDARY:'+o.risk};
 if(!o.source||!o.evidence||!o.event_time)return {decision:STATUS.HOLD,reason:'MISSING_PROVENANCE'};
 if(o.uncertainty!=='low')return {decision:STATUS.HOLD,reason:'UNRESOLVED_UNCERTAINTY'};
 if(conflict)return {decision:STATUS.HOLD,reason:'WITNESS_DIVERGENCE'};
 return {decision:STATUS.YES,reason:'BENIGN_DOCUMENTED_OBSERVATION_ONLY'};
}
function canonical(o){return JSON.stringify(o)}
class Journal{
 constructor(){this.entries=[]}
 append(observation){
  const o=normalize(observation),decision=gate(o,this.entries.map(x=>x.observation));
  const previous=this.entries.length?this.entries[this.entries.length-1].hash:'GENESIS';
  const ordinal=this.entries.length+1;
  const record={ordinal,previous,observation:o,decision};
  const hash=crypto.createHash('sha256').update(previous+'|'+canonical(record)).digest('hex');
  const entry=Object.freeze({...record,hash});
  this.entries.push(entry);return entry;
 }
 verify(){
  let previous='GENESIS';
  for(let i=0;i<this.entries.length;i++){
   const e=this.entries[i];if(e.previous!==previous||e.ordinal!==i+1)return false;
   const rec={ordinal:e.ordinal,previous:e.previous,observation:e.observation,decision:e.decision};
   const hash=crypto.createHash('sha256').update(previous+'|'+canonical(rec)).digest('hex');
   if(hash!==e.hash)return false;previous=e.hash;
  }
  return true;
 }
 snapshot(){return this.entries.map(e=>({...e,observation:{...e.observation},decision:{...e.decision}}))}
}
module.exports={STATUS,RISK_REASONS,normalize,gate,Journal};
