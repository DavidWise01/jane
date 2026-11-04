'use strict';
// B136 independent observations: no voting, no quorum, no automatic scientific truth.
const crypto=require('node:crypto');
const WITNESSES=Object.freeze(['a1','b1','c1']);
const hash=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
function frozen(x){if(x&&typeof x==='object'&&!Object.isFrozen(x)){Object.values(x).forEach(frozen);Object.freeze(x);}return x;}
function normalize(o){
 if(!o||typeof o!=='object'||!WITNESSES.includes(o.witness)||typeof o.event!=='string'||!o.event||typeof o.id!=='string'||!o.id||typeof o.source!=='string'||!o.source||typeof o.metric!=='string'||!o.metric||typeof o.unit!=='string'||!o.unit)throw Error('Witness, event, id, source, metric, and unit required');
 if(![o.lower,o.value,o.upper].every(x=>typeof x==='number'&&Number.isFinite(x))||o.lower>o.value||o.value>o.upper)throw Error('Invalid observation interval');
 if(!['INDEPENDENT','SHARED_OR_UNKNOWN'].includes(o.independence))throw Error('Independence status required');
 return frozen({id:o.id,event:o.event,witness:o.witness,source:o.source,metric:o.metric,unit:o.unit,lower:o.lower,value:o.value,upper:o.upper,independence:o.independence});
}
class WitnessLedger {
 constructor(){this.entries=[];}
 append(candidate){
  const observation=normalize(candidate);
  if(this.entries.some(x=>x.observation.id===observation.id))throw Error('Duplicate immutable observation ID');
  const body={sequence:this.entries.length+1,previous:this.entries.at(-1)?.hash||'GENESIS',observation};
  const e=frozen({...body,hash:hash(body)});this.entries.push(e);return e.hash;
 }
 compare(event,{externalEvidenceApproved=false}={}){
  if(typeof externalEvidenceApproved!=='boolean')throw Error('External evidence gate must be explicit boolean');
  const latest=WITNESSES.map(witness=>({witness,observation:this.entries.filter(e=>e.observation.event===event&&e.observation.witness===witness).at(-1)?.observation||null}));
  const reports=latest.filter(x=>x.observation).map(x=>x.observation);
  const missing=latest.filter(x=>!x.observation).map(x=>x.witness);
  const reasons=[];
  if(missing.length)reasons.push('MISSING_WITNESS_REPORT');
  if(reports.length&&new Set(reports.map(x=>x.metric+'\u0000'+x.unit)).size>1)reasons.push('INCOMPARABLE_METRICS_OR_UNITS');
  if(reports.some(x=>x.independence!=='INDEPENDENT'))reasons.push('INDEPENDENCE_NOT_ESTABLISHED');
  if(reports.length===3&&reports.every(x=>x.metric===reports[0].metric&&x.unit===reports[0].unit)){
   const lower=Math.max(...reports.map(x=>x.lower)), upper=Math.min(...reports.map(x=>x.upper));
   if(lower>upper)reasons.push('NON_OVERLAPPING_INTERVALS');
  }
  const compatible=reasons.length===0;
  if(!externalEvidenceApproved)reasons.push('EXTERNAL_EVIDENCE_NOT_APPROVED');
  const status=compatible&&externalEvidenceApproved?'ELIGIBLE_FOR_NEXT_GATE':'HOLD';
  return frozen({event,status,compatible,reported:reports.length,missing,observations:reports,reasons});
 }
 audit(){
  let previous='GENESIS';for(const [i,e] of this.entries.entries()){
   const {hash:observed,...body}=e;
   if(e.sequence!==i+1||e.previous!==previous||hash(body)!==observed)throw Error('Broken witness journal');
   previous=observed;
  }
  return {entries:this.entries.length,chainVerified:true,quorumUsed:false,votesUsed:false};
 }
}
module.exports={WITNESSES,normalize,WitnessLedger};
