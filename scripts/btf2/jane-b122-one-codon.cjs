'use strict';
const prior=require('./jane-b121-two-dots.cjs');
const CUBITS=2, SLOTS_PER_CUBIT=2**3, CODON_SIZE=16, CHOICE_POOL=20;
const candidates=Object.freeze([
 ...prior.NAMES.map((x,i)=>Object.freeze({...x,choice_id:'C'+String(i).padStart(2,'0')})),
 ...[16,17,18,19].map(i=>Object.freeze({name:null,role:null,discipline:null,parent:null,status:'unassigned',choice_id:'C'+String(i).padStart(2,'0')}))
]);
function codon(choiceIds=candidates.slice(0,16).map(x=>x.choice_id)){
 if(!Array.isArray(choiceIds)||choiceIds.length!==CODON_SIZE||new Set(choiceIds).size!==CODON_SIZE)throw Error('Codon requires 16 distinct choices');
 const selected=choiceIds.map(id=>{const entry=candidates.find(c=>c.choice_id===id);if(!entry)throw Error('Unknown choice '+id);return entry});
 for(let i=0;i<11;i++)if(!selected.some(s=>s.choice_id==='C'+String(i).padStart(2,'0')))throw Error('Missing frozen foundation choice C'+String(i).padStart(2,'0'));
 return selected.map((c,i)=>({...c,cubit:Math.floor(i/SLOTS_PER_CUBIT),slot:i%SLOTS_PER_CUBIT,address:'CODON001:CU'+Math.floor(i/SLOTS_PER_CUBIT)+':'+(i%SLOTS_PER_CUBIT).toString(2).padStart(3,'0')}));
}
function audit(){
 const selected=codon(),addresses=new Set(selected.map(x=>x.address));
 if(candidates.length!==CHOICE_POOL||addresses.size!==16||selected.filter(x=>x.status==='established').length!==11)throw Error('Codon invariant failed');
 const defaults=selected.filter(x=>x.status==='proposed').length;
 return {name:'ONE CODON',cubit_count:CUBITS,slots_per_cubit:SLOTS_PER_CUBIT,lineage_slots:CODON_SIZE,choice_pool:CHOICE_POOL,foundation_locked:11,default_proposed:defaults,unassigned_choices:4,unique_addresses:addresses.size,implementation:'LOGICAL_NOT_BIOLOGICAL_OR_QUANTUM_ENTANGLEMENT'};
}
module.exports={CUBITS,SLOTS_PER_CUBIT,CODON_SIZE,CHOICE_POOL,candidates,codon,audit};
