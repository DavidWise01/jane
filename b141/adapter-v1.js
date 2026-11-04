(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.JaneB141=api;
})(typeof globalThis==='object'?globalThis:this,function(){
'use strict';
const ORDER=['RED','BLUE','GREEN','BLACK','WHITE','GRAY','YELLOW','ROYAL PURPLE'];
const expected=[
'Jane','Toph','Patricia','Lilith','a.t.o.m','E.V.E','Icarium','Mary M',
'Holly','Vicky V.','LeeLuu','Sola','Vita','Mira','Pax','Nexa'];
const isString=x=>typeof x==='string'&&x.length>0;
function validate(x){
 const errors=[];
 if(!x||typeof x!=='object')return{ok:false,errors:['Missing evidence document']};
 if(x.schema!=='JANE-B141-READONLY-EVIDENCE-v1')errors.push('Wrong schema');
 if(x.releaseStatus!=='HOLD')errors.push('Unattested release status must remain HOLD');
 if(!Array.isArray(x.colors)||ORDER.some((v,i)=>x.colors[i]!==v)||x.colors.length!==8)errors.push('Canonical colors changed');
 if(!Array.isArray(x.cortex)||x.cortex.length!==16)errors.push('Exactly sixteen cortexes required');
 else{
  const addresses=new Set(),names=new Set();
  x.cortex.forEach((m,i)=>{
   if(!m||m.name!==expected[i]||m.cubit!==Math.floor(i/8)||m.address!==(i%8).toString(2).padStart(3,'0')||m.channel!==ORDER[i%8]||m.active!==(i===15))errors.push('Invalid cortex at '+i);
   if(m){addresses.add(m.cubit+':'+m.address);names.add(m.name);}
  });
  if(addresses.size!==16||names.size!==16)errors.push('Duplicate cortex identity');
 }
 if(!Array.isArray(x.elements)||x.elements.length!==11)errors.push('Expected eleven scoped elements');
 else {
  let total=0;const unique=new Set();
  x.elements.forEach(e=>{
   if(!e||!Number.isInteger(e.Z)||!isString(e.symbol)||!Array.isArray(e.masses)||!isString(e.source)||!e.source.startsWith('https://')){errors.push('Invalid element');return}
   if(unique.has(e.Z))errors.push('Duplicate atomic number');unique.add(e.Z);
   for(const a of e.masses){if(!Number.isInteger(a)||a<e.Z)errors.push('Invalid isotope mass');else total++;}
  });
  if(total!==26)errors.push('Expected 26 natural-composition isotope records');
 }
 if(!Array.isArray(x.reactions)||x.reactions.length!==5)errors.push('Expected five sample reactions');
 else for(const edge of x.reactions)if(!edge||!isString(edge.id)||!Array.isArray(edge.inputs)||!Array.isArray(edge.outputs)||!['NEW_GRANDMA','INTERMEDIATE_ONLY'].includes(edge.outcome)||!isString(edge.source))errors.push('Invalid sample reaction');
 if(!Array.isArray(x.witnesses)||x.witnesses.length!==3||['a1','b1','c1'].some((v,i)=>x.witnesses?.[i]?.id!==v))errors.push('Witness identity mismatch');
 else x.witnesses.forEach(w=>{if(w.sourceType!=='synthetic'||!Array.isArray(w.interval)||w.interval.length!==3||w.interval.some(v=>typeof v!=='number'||!Number.isFinite(v))||w.interval[0]>w.interval[1]||w.interval[1]>w.interval[2])errors.push('Invalid witness interval')});
 if(!x.provenance||!Object.values(x.provenance).every(isString))errors.push('Missing provenance');
 return {ok:errors.length===0,errors,summary:{cortexes:x.cortex?.length||0,elements:x.elements?.length||0,isotopeEntries:x.elements?.reduce((n,e)=>n+(e.masses?.length||0),0)||0,reactions:x.reactions?.length||0,witnesses:x.witnesses?.length||0}};
}
return Object.freeze({validate,ORDER});
});
