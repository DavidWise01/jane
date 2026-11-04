'use strict';
// B132: Immutable trial genealogy; failed trials may motivate variations, never
// become accepted ancestors. No laboratory operation or physical prediction.
const crypto=require('node:crypto');
const REQUIRED=Object.freeze(['nuclear','chemical','environment','provenance','repeatability']);
const deepFreeze=x=>{if(x&&typeof x==='object'&&!Object.isFrozen(x)){for(const v of Object.values(x))deepFreeze(v);Object.freeze(x)}return x};
function validate(c){
 if(!c||typeof c!=='object'||typeof c.id!=='string'||!c.id.trim()||typeof c.configuration!=='string'||!c.configuration.trim()||typeof c.environment!=='string'||!c.environment.trim()||typeof c.evidence!=='string'||!c.evidence.trim())throw Error('Full trial identity, context and evidence required');
 if(c.origin!==undefined && c.origin!==null && typeof c.origin!=='string')throw Error('Invalid origin reference');
 if(c.parentAccepted!==undefined && c.parentAccepted!==null && typeof c.parentAccepted!=='string')throw Error('Invalid parent reference');
 if(!c.gates||typeof c.gates!=='object')throw Error('Gates required');
 for(const k of REQUIRED){if(!['PASS','FAIL','UNKNOWN'].includes(c.gates[k]))throw Error('Invalid or missing gate '+k)}
 return deepFreeze({id:c.id,configuration:c.configuration,environment:c.environment,evidence:c.evidence,origin:c.origin||null,parentAccepted:c.parentAccepted||null,gates:Object.fromEntries(REQUIRED.map(k=>[k,c.gates[k]]))});
}
function decision(c){const failed=REQUIRED.filter(k=>c.gates[k]==='FAIL'),unknown=REQUIRED.filter(k=>c.gates[k]==='UNKNOWN');return {status:failed.length?'REJECT':unknown.length?'HOLD':'PROMOTE',failed,unknown}}
class Trainer{
 constructor(){this.events=[];this.active=new Map()}
 submit(candidate){
  const c=validate(candidate);
  if(this.events.some(e=>e.candidate.id===c.id))throw Error('Duplicate immutable trial id');
  if(c.origin&&!this.events.some(e=>e.candidate.id===c.origin))throw Error('Unknown origin');
  if(c.parentAccepted&&!this.active.has(c.parentAccepted))throw Error('Accepted parent required');
  if(c.origin===c.id||c.parentAccepted===c.id)throw Error('Self reference');
  const verdict=deepFreeze(decision(c));
  const previous=this.events.length?this.events.at(-1).hash:'GENESIS';
  const payload=deepFreeze({ordinal:this.events.length+1,previous,candidate:c,verdict});
  const hash=crypto.createHash('sha256').update(JSON.stringify(payload)).digest('hex');
  const entry=deepFreeze({...payload,hash});
  this.events.push(entry);
  if(verdict.status==='PROMOTE')this.active.set(c.id,hash);
  return {id:c.id,decision:verdict.status,hash,origin:c.origin,parentAccepted:c.parentAccepted};
 }
 verify(){
  let prev='GENESIS',promoted=0;
  for(let i=0;i<this.events.length;i++){
   const e=this.events[i];
   if(e.ordinal!==i+1||e.previous!==prev)throw Error('Journal order mismatch');
   const payload={ordinal:e.ordinal,previous:e.previous,candidate:e.candidate,verdict:e.verdict};
   const hash=crypto.createHash('sha256').update(JSON.stringify(payload)).digest('hex');
   if(hash!==e.hash)throw Error('Tamper detected');
   if(e.verdict.status==='PROMOTE'){promoted++;if(this.active.get(e.candidate.id)!==e.hash)throw Error('Active pool mismatch')}
   else if(this.active.has(e.candidate.id))throw Error('Failed or unknown trial promoted');
   if(e.candidate.parentAccepted){
    const p=this.events.find(x=>x.candidate.id===e.candidate.parentAccepted);
    if(!p||p.verdict.status!=='PROMOTE'||p.ordinal>=e.ordinal)throw Error('Invalid inherited parent');
   }
   if(e.candidate.origin){
    const origin=this.events.find(x=>x.candidate.id===e.candidate.origin);
    if(!origin||origin.ordinal>=e.ordinal)throw Error('Origin forward reference');
   }
   prev=e.hash;
  }
  if(promoted!==this.active.size)throw Error('Active pool count mismatch');
  return {observed:this.events.length,promoted,rejected:this.events.filter(e=>e.verdict.status==='REJECT').length,held:this.events.filter(e=>e.verdict.status==='HOLD').length,verified:true,failed_in_active_pool:0};
 }
}
module.exports={REQUIRED,validate,decision,Trainer};
