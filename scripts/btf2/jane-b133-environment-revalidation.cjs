'use strict';
// B133: environment-specific acceptance; immutable prior outcomes.
const crypto=require('node:crypto');
const GATES=Object.freeze(['nuclear','chemical','environment','provenance','repeatability']);
const STATUSES=new Set(['PASS','FAIL','UNKNOWN']);
const stable=x=>{if(x&&typeof x==='object'&&!Object.isFrozen(x)){for(const v of Object.values(x))stable(v);Object.freeze(x)}return x;};
const hash=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
function normalize(input){
 if(!input||typeof input!=='object')throw Error('Invalid trial');
 for(const k of ['id','configuration','environment','evidence'])if(typeof input[k]!=='string'||!input[k].trim())throw Error('Missing '+k);
 if(input.origin!==undefined&&input.origin!==null&&typeof input.origin!=='string')throw Error('Invalid origin');
 if(input.parentAccepted!==undefined&&input.parentAccepted!==null&&typeof input.parentAccepted!=='string')throw Error('Invalid parentAccepted');
 if(!input.gates||typeof input.gates!=='object')throw Error('Missing gates');
 const gates={};for(const g of GATES){if(!STATUSES.has(input.gates[g]))throw Error('Invalid gate '+g);gates[g]=input.gates[g];}
 return stable({id:input.id,configuration:input.configuration,environment:input.environment,evidence:input.evidence,origin:input.origin||null,parentAccepted:input.parentAccepted||null,gates});
}
function classify(gates){const failures=GATES.filter(g=>gates[g]==='FAIL');const unknown=GATES.filter(g=>gates[g]==='UNKNOWN');return stable({status:failures.length?'REJECT':unknown.length?'HOLD':'PROMOTE',failures,unknown});}
class Trainer{
 constructor(){this.journal=[];this.active=new Map();}
 submit(input){
  const c=normalize(input);
  if(this.journal.some(e=>e.candidate.id===c.id))throw Error('Immutable ID already exists');
  if(c.origin&&!this.journal.some(e=>e.candidate.id===c.origin))throw Error('Unknown origin');
  if(c.parentAccepted&&!this.active.has(c.parentAccepted))throw Error('Parent not accepted');
  if(c.parentAccepted){const p=this.journal.find(e=>e.candidate.id===c.parentAccepted);if(p.candidate.configuration!==c.configuration)throw Error('Inherited parent must have same configuration; changed design requires fresh lineage');}
  const result=classify(c.gates);
  const payload=stable({ordinal:this.journal.length+1,previous:this.journal.at(-1)?.hash||'GENESIS',candidate:c,result});
  const event=stable({...payload,hash:hash(payload)});
  this.journal.push(event);
  if(result.status==='PROMOTE')this.active.set(c.id,event.hash);
  return {id:c.id,status:result.status,eventHash:event.hash};
 }
 current(configuration,environment){
  const candidates=this.journal.filter(e=>e.candidate.configuration===configuration&&e.candidate.environment===environment);
  if(!candidates.length)return {status:'UNTESTED',authorized:false,trial:null};
  const e=candidates.at(-1);
  return {status:e.result.status,authorized:e.result.status==='PROMOTE',trial:e.candidate.id};
 }
 transfer(id,newEnvironment){
  const source=this.journal.find(e=>e.candidate.id===id);
  if(!source)throw Error('Unknown source');
  return {configuration:source.candidate.configuration,environment:newEnvironment,status:'UNTESTED',authorized:false,source:id};
 }
 verify(){
  let previous='GENESIS',accepted=0;
  for(const [i,e] of this.journal.entries()){
   const {hash:observed,...payload}=e;
   if(e.ordinal!==i+1||e.previous!==previous||hash(payload)!==observed)throw Error('Audit chain invalid');
   if(e.result.status==='PROMOTE'){accepted++;if(this.active.get(e.candidate.id)!==observed)throw Error('Active pool inconsistent');}
   else if(this.active.has(e.candidate.id))throw Error('Failed/held record in active pool');
   if(e.candidate.origin){const idx=this.journal.findIndex(x=>x.candidate.id===e.candidate.origin);if(idx<0||idx>=i)throw Error('Invalid origin ancestry');}
   if(e.candidate.parentAccepted){const idx=this.journal.findIndex(x=>x.candidate.id===e.candidate.parentAccepted);if(idx<0||idx>=i||this.journal[idx].result.status!=='PROMOTE')throw Error('Invalid accepted parent');}
   previous=observed;
  }
  if(accepted!==this.active.size)throw Error('Accepted pool count invalid');
  return {observations:this.journal.length,promoted:accepted,held:this.journal.filter(e=>e.result.status==='HOLD').length,rejected:this.journal.filter(e=>e.result.status==='REJECT').length,appendOnly:true,verified:true};
 }
}
module.exports={GATES,normalize,classify,Trainer};
