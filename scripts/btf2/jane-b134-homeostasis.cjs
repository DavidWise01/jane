'use strict';
// B134: homeostasis across a declared finite environment matrix.
// 100% denotes the declared test set, not universal physical stability.
const crypto=require('node:crypto');
const hash=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const GATES=['nuclear','chemical','environment','provenance','repeatability'];
const OUTCOMES=new Set(['PASS','FAIL','UNKNOWN']);
function review(gates){
 if(!gates||GATES.some(k=>!OUTCOMES.has(gates[k])))throw Error('Every gate must be PASS/FAIL/UNKNOWN');
 return GATES.some(k=>gates[k]==='FAIL')?'REJECT':GATES.some(k=>gates[k]==='UNKNOWN')?'HOLD':'PASS';
}
class Homeostasis {
 constructor(config,contexts){
  if(!config||!Array.isArray(contexts)||!contexts.length||new Set(contexts).size!==contexts.length||contexts.some(x=>typeof x!=='string'||!x.trim()))throw Error('Declare nonempty unique environments');
  this.config=config;this.contexts=Object.freeze([...contexts]);this.events=[];
 }
 submit({id,context,gates,evidence,origin=null}){
  if(typeof id!=='string'||!id||!this.contexts.includes(context)||typeof evidence!=='string'||!evidence.trim()||this.events.some(e=>e.id===id))throw Error('Invalid/duplicate trial or missing evidence');
  if(origin!==null&&!this.events.some(e=>e.id===origin))throw Error('Unknown origin');
  const outcome=review(gates);
  const body={ordinal:this.events.length+1,id,context,gates:{...gates},evidence,origin,outcome,previous:this.events.at(-1)?.hash||'GENESIS'};
  const event=Object.freeze({...body,gates:Object.freeze(body.gates),hash:hash(body)});
  this.events.push(event);return{id,outcome};
 }
 report(){
  const each=this.contexts.map(context=>{const history=this.events.filter(e=>e.context===context),current=history.at(-1);return{context,status:current?.outcome||'UNTESTED',latest:current?.id||null}});
  const counts={PASS:0,HOLD:0,REJECT:0,UNTESTED:0};each.forEach(x=>counts[x.status]++);
  return {config:this.config,contexts:this.contexts.length,counts,coveragePercent:100*(this.contexts.length-counts.UNTESTED)/this.contexts.length,currentPassPercent:100*counts.PASS/this.contexts.length,decision:counts.PASS===this.contexts.length?'PROMOTE':'HOLD',perContext:each};
 }
 audit(){
  let prev='GENESIS';for(const [i,e] of this.events.entries()){const {hash:recorded,...body}=e;if(e.ordinal!==i+1||e.previous!==prev||hash(body)!==recorded||review(e.gates)!==e.outcome)throw Error('Journal violation');prev=recorded;}
  const r=this.report();return{entries:this.events.length,chainVerified:true,invalidPromotions:r.decision==='PROMOTE'&&r.counts.PASS!==this.contexts.length?1:0};
 }
}
module.exports={GATES,review,Homeostasis};
