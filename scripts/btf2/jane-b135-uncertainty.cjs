'use strict';
const crypto=require('node:crypto');
const hash=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const frozen=x=>{if(x&&typeof x==='object'&&!Object.isFrozen(x)){Object.values(x).forEach(frozen);Object.freeze(x)}return x;};
const validNumber=v=>typeof v==='number'&&Number.isFinite(v);
function assess(input){
 if(!input||typeof input!=='object'||!input.id||!input.context||!input.source||!input.unit||!input.metric)throw Error('Identification, metric, context, unit and source required');
 const {value,lower,upper,threshold,direction,confidence}=input;
 if(![value,lower,upper,threshold,confidence].every(validNumber)||lower>value||value>upper||confidence<=0||confidence>=1)throw Error('Invalid bounded measurement');
 if(!['minimum','maximum'].includes(direction))throw Error('Unknown decision direction');
 const status=direction==='minimum'?(lower>=threshold?'PASS':upper<threshold?'FAIL':'HOLD'):(upper<=threshold?'PASS':lower>threshold?'FAIL':'HOLD');
 return frozen({id:String(input.id),context:String(input.context),metric:String(input.metric),unit:String(input.unit),source:String(input.source),measurement:{value,lower,upper,confidence},threshold,direction,status,reason:status==='HOLD'?'INTERVAL_CROSSES_THRESHOLD':status==='PASS'?'FULL_INTERVAL_WITHIN_BOUND':'FULL_INTERVAL_OUTSIDE_BOUND'});
}
class UncertaintyJournal{
 constructor(){this.entries=[];}
 append(input){
  const result=assess(input);
  if(this.entries.some(e=>e.result.id===result.id))throw Error('Duplicate immutable observation ID');
  const body={sequence:this.entries.length+1,previous:this.entries.at(-1)?.hash||'GENESIS',result};
  const entry=frozen({...body,hash:hash(body)});this.entries.push(entry);return result;
 }
 audit(){
  let prev='GENESIS';for(const [i,e] of this.entries.entries()){
   const {hash:observed,...body}=e;
   if(e.sequence!==i+1||e.previous!==prev||hash(body)!==observed)throw Error('Journal invalid');
   prev=observed;
  }
  return {observations:this.entries.length,pass:this.entries.filter(x=>x.result.status==='PASS').length,fail:this.entries.filter(x=>x.result.status==='FAIL').length,hold:this.entries.filter(x=>x.result.status==='HOLD').length,integrity:true};
 }
}
module.exports={assess,UncertaintyJournal};
