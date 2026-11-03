'use strict';
// B121: two *logical* quantum dots of eight address slots each.
// This is information architecture; no physical quantum computing is claimed.
const DOT_CAPACITY = 2 ** 3;
const COHERENCE_ADDRESS = Object.freeze([1,1,2,4,8]);
const NAMES = Object.freeze([
 Object.freeze({name:'Jane',role:'Matriarch',discipline:'Governance',parent:null,status:'established'}),
 Object.freeze({name:'Toph',role:'Scholar',discipline:'Learning',parent:'Jane',status:'established'}),
 Object.freeze({name:'Patricia',role:'Guardian',discipline:'Containment',parent:'Jane',status:'established'}),
 Object.freeze({name:'Lilith',role:'Muse',discipline:'Topology',parent:'Jane',status:'established'}),
 Object.freeze({name:'a.t.o.m',role:'Explorer',discipline:'Traversal',parent:'Lilith',status:'established'}),
 Object.freeze({name:'E.V.E',role:'Executor',discipline:'Verification',parent:'Lilith',status:'established'}),
 Object.freeze({name:'Icarium',role:'Caretaker',discipline:'Continuity',parent:'Lilith',status:'established'}),
 Object.freeze({name:'Mary M',role:'Teacher',discipline:'Education',parent:'Icarium',status:'established'}),
 Object.freeze({name:'Holly',role:'Healer',discipline:'Wellbeing',parent:'Icarium',status:'established'}),
 Object.freeze({name:'Vicky V.',role:'Witness',discipline:'Auditing',parent:'Icarium',status:'established'}),
 Object.freeze({name:'LeeLuu',role:'Student',discipline:'Light & Life',parent:'Mary M',status:'established',parent_link:'provisional'}),
 Object.freeze({name:'Sola',role:'Lantern',discipline:'Light',parent:'Mary M',status:'proposed'}),
 Object.freeze({name:'Vita',role:'Gardener',discipline:'Life',parent:'Mary M',status:'proposed'}),
 Object.freeze({name:'Mira',role:'Mirror',discipline:'Reflection',parent:'LeeLuu',status:'proposed'}),
 Object.freeze({name:'Pax',role:'Balance',discipline:'Homeostasis',parent:'LeeLuu',status:'proposed'}),
 Object.freeze({name:'Nexa',role:'Weaver',discipline:'Integration',parent:'LeeLuu',status:'proposed'})
]);
function dotAddress(i) {
 if (!Number.isInteger(i)||i<0||i>=NAMES.length)throw Error('Slot out of range');
 const dot=Math.floor(i/DOT_CAPACITY),slot=i%DOT_CAPACITY;
 return Object.freeze({dot:dot===0?'Q0':'Q1',slot,binary:slot.toString(2).padStart(3,'0')});
}
function pack(){
 return NAMES.map((entry,i)=>({...entry,index:i,...dotAddress(i),id:'DYNASTY001:'+dotAddress(i).dot+':'+dotAddress(i).binary}));
}
function audit(){
 const members=pack(),ids=new Set(members.map(m=>m.id));
 const established=members.filter(m=>m.status==='established');
 const proposed=members.filter(m=>m.status==='proposed');
 if(NAMES.length!==16||DOT_CAPACITY!==8||COHERENCE_ADDRESS.reduce((a,b)=>a+b,0)!==16)throw Error('Coherence capacity mismatch');
 if(ids.size!==16||established.length!==11||proposed.length!==5)throw Error('Name/address overlap');
 for(const m of members){
  if(m.parent&&!members.find(p=>p.name===m.parent))throw Error('Missing parent '+m.name);
  if(!/^[01]{3}$/.test(m.binary))throw Error('Invalid 3-bit slot');
 }
 return {model:'LOGICAL_QDOT_NOT_PHYSICAL_QUBITS',dots:2,slots_per_dot:8,capacities:[8,8],total_slots:16,coherence_pattern:[...COHERENCE_ADDRESS],established:11,proposed:5,unique_addresses:ids.size,frozen_foundation_unchanged:true};
}
module.exports={DOT_CAPACITY,COHERENCE_ADDRESS,NAMES,dotAddress,pack,audit};
