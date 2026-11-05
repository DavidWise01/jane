'use strict';
const crypto=require('node:crypto');
const base=require('./jane-b157-pre-isa-boundary.cjs');
const REGS=Object.freeze(['a','b','c']);
const hash=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
function ownership(global){
 const a=base.decode(global);
 return a?Object.freeze({...a,authority:'SOURCE_REGISTER',readThroughD:true,physicalPromotion:false}):null;
}
function containment(src=base.sources()){
 const test=base.audit(src);
 if(test.status!=='STRUCTURAL_PASS')return{status:'HOLD',reason:'SOURCE_INTEGRITY',detail:test.errors};
 const d=base.assemble(src);
 const countBySource=Object.fromEntries(REGS.map(r=>[r,d.filter(x=>x.register===r).length]));
 return {status:'STRUCTURAL_PASS',sourceRegisters:3,countBySource,derivedLength:d.length,derivedAllocation:0,disjoint:true,isaDefined:false,quorum:false,physicalPromotion:false};
}
function boundary(fromGlobal,toGlobal,sign){
 const from=ownership(fromGlobal),to=ownership(toGlobal);
 if(!from||!to||!['+','-'].includes(sign))return{status:'HOLD',reason:'INVALID_BOUNDARY_INPUT',physicalPromotion:false};
 const expected=sign==='+'?fromGlobal%366+1:(fromGlobal+364)%366+1;
 if(toGlobal!==expected)return{status:'HOLD',reason:'NON_ADJACENT_GLOBAL_ADDRESS',physicalPromotion:false};
 const registerChange=from.register!==to.register;
 const regionChange=from.local<=62!== (to.local<=62);
 // D is read-only: crossing into a new source authority requires a separate
 // observation from that source, not an automatic write or authorization.
 const kind=registerChange?'SOURCE_AUTHORITY_SEAM':regionChange?'BOX_TOROID_SEAM':'INTRA_SOURCE';
 return {status:registerChange?'HOLD_SOURCE_WITNESS_REQUIRED':'SYMBOLIC_BOUNDARY',kind,from,to,sign,changesSource:registerChange,needsWitness:registerChange?to.witness:null,physicalPromotion:false};
}
function witnessRecord({register,local,observationId,note=''}) {
 const a=base.address(register,local);
 if(!a||typeof observationId!=='string'||!observationId.trim())throw Error('INVALID_WITNESS_OBSERVATION');
 if(typeof note!=='string')throw Error('NOTE_MUST_BE_TEXT');
 return Object.freeze({observationId,register,owner:REGS.includes(register)?base.REG[register].witness:null,local,global:a.global,note,kind:'USER_DEFINED_SYMBOLIC_OBSERVATION',physicalPromotion:false});
}
class WitnessLedgers{
 constructor(){this.logs={a:[],b:[],c:[]}}
 append(record){
  if(!record||!REGS.includes(record.register)||record.owner!==base.REG[record.register].witness||base.address(record.register,record.local)?.global!==record.global||record.physicalPromotion!==false)throw Error('FOREIGN_OR_INVALID_RECORD');
  if(REGS.some(r=>this.logs[r].some(e=>e.record.observationId===record.observationId)))throw Error('DUPLICATE_ID');
  const log=this.logs[record.register],payload={seq:log.length+1,previous:log.at(-1)?.hash||'GENESIS',record:JSON.parse(JSON.stringify(record))};
  const entry=Object.freeze({...payload,hash:hash(payload)});log.push(entry);return entry;
 }
 view(){return REGS.flatMap(r=>this.logs[r].map(e=>Object.freeze({register:r,record:e.record,hash:e.hash})))}
 audit(){
  for(const r of REGS){let prev='GENESIS';const log=this.logs[r];
   for(let i=0;i<log.length;i++){const entry=log[i],{hash:provided,...body}=entry;
    if(body.seq!==i+1||body.previous!==prev||hash(body)!==provided||body.record.register!==r||body.record.owner!==base.REG[r].witness||body.record.physicalPromotion!==false)return{status:'HOLD',source:r,reason:'WITNESS_CHAIN_OR_OWNER'};
    prev=provided;
   }
  }
  return{status:'PASS',witnessCounts:Object.fromEntries(REGS.map(r=>[r,this.logs[r].length])),derivedViewEntries:this.view().length,quorum:false,physicalPromotion:false};
 }
}
module.exports={REGS,ownership,containment,boundary,witnessRecord,WitnessLedgers};
