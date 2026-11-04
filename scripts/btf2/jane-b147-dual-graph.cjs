'use strict';
const ORDER=Object.freeze(['sag a','nib sun','nib','earth','earth sun']);
const CORE=Object.freeze(ORDER.slice(0,4));
const PAIRS=Object.freeze([[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]]);
const SLOTS=Object.freeze([
['u1','x²',0,1,'long','weak+gravity'],['u2','y²',1,2,'medium','medium'],
['u3','z²',2,3,'medium','medium+weak'],['u4','x²::y²',3,4,'short','medium+strong'],
['u5','y²::z²',0,2,'unquantified','epicycle'],['u6','z²::x²',0,3,'unquantified','double epicycle']
]);
const key=(a,b)=>[a,b].sort().join('|');
function build(){
 const force=SLOTS.map(([id,notation,a,b,distanceBand,forceBand])=>({id,notation,from:ORDER[a],to:ORDER[b],distanceBand,forceBand,classification:a===3&&b===4?'TERMINAL_LINK':'CORE_FORCE',status:'DECLARED_NOT_MEASURED'}));
 const byKey=new Map(force.map(e=>[key(e.from,e.to),e]));
 const geometry=PAIRS.map(([a,b])=>{const from=CORE[a],to=CORE[b],e=byKey.get(key(from,to));return{id:`g${a}${b}`,from,to,kind:'GEOMETRIC_PAIR',sourceForceId:e?e.id:null,distanceMeters:null,sourceStatus:e?'SOURCE_FORCE_PAIR_MATCH':'UNBOUND_GEOMETRIC_PAIR'};});
 return{schema:'JANE-B147-DUAL-GRAPH-v1',order:[...ORDER],core:[...CORE],terminal:ORDER[4],force,geometry,matched:geometry.filter(e=>e.sourceForceId!==null).length,missing:geometry.filter(e=>e.sourceForceId===null).map(e=>[e.from,e.to]),terminalLinks:force.filter(e=>e.classification==='TERMINAL_LINK').length,physicalStatus:'HOLD',combinedClockRate:'HOLD'};
}
function audit(d){
 const errors=[],expected=build();
 if(!d||d.schema!==expected.schema)errors.push('SCHEMA');
 if(JSON.stringify(d?.order)!==JSON.stringify(expected.order))errors.push('ORDER');
 if(JSON.stringify(d?.core)!==JSON.stringify(expected.core)||d?.terminal!==expected.terminal)errors.push('CORE_TERMINAL');
 for(const f of ['force','geometry'])if(JSON.stringify(d?.[f])!==JSON.stringify(expected[f]))errors.push('ALTERED_'+f.toUpperCase());
 if(d?.matched!==5||d?.terminalLinks!==1||JSON.stringify(d?.missing)!==JSON.stringify([['nib sun','earth']]))errors.push('MISMATCH_PRESERVATION');
 if(d?.physicalStatus!=='HOLD'||d?.combinedClockRate!=='HOLD')errors.push('UNVERIFIED_PHYSICS');
 return{status:errors.length?'HOLD':'STRUCTURAL_PASS_WITH_UNBOUND_EDGE',errors,forceEdges:d?.force?.length||0,geometricPairs:d?.geometry?.length||0,matched:d?.matched,unbound:d?.missing};
}
module.exports={ORDER,CORE,PAIRS,SLOTS,key,build,audit};
