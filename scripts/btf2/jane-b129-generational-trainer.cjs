'use strict';
// B129: model trainer with failure retained as evidence, but never promoted.
// "Gene pool" here refers to candidate configurations in a simulation.
const crypto=require('node:crypto');
const REQUIRED=Object.freeze(['conservation','stability','provenance','repeatability']);
function evaluate(candidate){
 if(!candidate || typeof candidate!=='object' || !candidate.id)throw Error('Candidate id required');
 const gates={};for(const name of REQUIRED)gates[name]=candidate.gates?.[name]===true;
 const failed=REQUIRED.filter(k=>!gates[k]);
 return {id:String(candidate.id),promote:failed.length===0,failed,gates,decision:failed.length===0?'PROMOTE':'RETAIN_FAILURE_ONLY'};
}
class Trainer{
 constructor(){this.events=[];this.genePool=[];this.genesis='GENESIS'}
 submit(candidate){
  const result=evaluate(candidate);
  if(this.events.some(e=>e.id===result.id))throw Error('Duplicate id; retries need distinct IDs');
  const previous=this.events.at(-1)?.hash||this.genesis;
  const event={ordinal:this.events.length+1,id:result.id,previous,result,observed:structuredClone(candidate)};
  event.hash=crypto.createHash('sha256').update(JSON.stringify(event)).digest('hex');
  this.events.push(event);
  if(result.promote)this.genePool.push({id:result.id,eventHash:event.hash});
  return {decision:result.decision,failed:[...result.failed],hash:event.hash};
 }
 audit(){
  const promoted=this.events.filter(e=>e.result.promote);
  if(promoted.length!==this.genePool.length)throw Error('Pool mismatch');
  const promotedHashes=new Set(promoted.map(e=>e.hash));
  if(this.genePool.some(m=>!promotedHashes.has(m.eventHash)))throw Error('Failure entered active pool');
  let previous=this.genesis;
  for(const e of this.events){
   if(e.previous!==previous)throw Error('Chain broken');
   const {hash,...rest}=e;
   if(crypto.createHash('sha256').update(JSON.stringify(rest)).digest('hex')!==hash)throw Error('Journal mutated');
   previous=hash;
  }
  return {observations:this.events.length,promoted:promoted.length,rejected:this.events.length-promoted.length,failed_in_active_pool:0,verified:true};
 }
}
module.exports={REQUIRED,evaluate,Trainer};
