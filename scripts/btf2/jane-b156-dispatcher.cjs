'use strict';
const crypto=require('node:crypto');
const {assemble,address,decode,assertComposition}=require('./jane-b155-isa.cjs');
const REG=['a','b','c'],OPS=['STEP','READ','WITNESS','ASSEMBLE','CHECK','INTERRUPT','RESUME'];
const hash=obj=>crypto.createHash('sha256').update(JSON.stringify(obj)).digest('hex');
const stable=x=>JSON.parse(JSON.stringify(x));
function initial(){return {pc:{a:1,b:1,c:1},halted:false,checkpoint:null,dispatchCount:0}}
function route(cmd){
 if(!cmd||cmd.via!=='d'||!OPS.includes(cmd.opcode))return {error:'INVALID_D_INSTRUCTION'};
 if(cmd.opcode==='STEP'||cmd.opcode==='READ'||cmd.opcode==='WITNESS'){
   if(cmd.global!==undefined){
     let decoded;try{decoded=decode(cmd.global)}catch(_){return{error:'ADDRESS_OUT_OF_RANGE'}}
     if(cmd.register&&cmd.register!==decoded.register)return{error:'REGISTER_ADDRESS_MISMATCH'};
     return {register:decoded.register,local:decoded.local,global:decoded.global};
   }
   if(!REG.includes(cmd.register))return{error:'INVALID_SOURCE_REGISTER'};
   if(cmd.local!==undefined){try{return address(cmd.register,cmd.local)}catch(_){return{error:'LOCAL_OUT_OF_RANGE'}}}
   return {register:cmd.register};
 }
 return {};
}
function apply(state,cmd){
 const routeResult=route(cmd);
 if(routeResult.error)return{status:'HOLD',reason:routeResult.error,physicalPromotion:false};
 const op=cmd.opcode;
 if(state.halted&&op!=='RESUME'&&op!=='CHECK')return{status:'HOLD',reason:'INTERRUPTED_NO_SOURCE_MUTATION',physicalPromotion:false};
 if(op==='INTERRUPT'){
   if(state.halted)return{status:'HOLD',reason:'ALREADY_HALTED',physicalPromotion:false};
   state.halted=true;const snapshot={pc:stable(state.pc),dispatchCount:state.dispatchCount};
   state.checkpoint={...snapshot,hash:hash(snapshot)};
   return{status:'INTERRUPTED',checkpoint:stable(state.checkpoint),physicalPromotion:false};
 }
 if(op==='RESUME'){
   if(!state.halted||!state.checkpoint)return{status:'HOLD',reason:'NO_ACTIVE_CHECKPOINT',physicalPromotion:false};
   const {hash:expected,...snapshot}=state.checkpoint;
   if(expected!==hash(snapshot)||JSON.stringify(snapshot.pc)!==JSON.stringify(state.pc)||snapshot.dispatchCount!==state.dispatchCount)return{status:'HOLD',reason:'CHECKPOINT_INVALID',physicalPromotion:false};
   state.halted=false;
   return{status:'RESUMED',checkpointHash:expected,physicalPromotion:false};
 }
 if(op==='ASSEMBLE')return{status:'PASS',d:{length:366,sourceRegisters:3,additionalCells:0},physicalPromotion:false};
 if(op==='CHECK')return{status:assertComposition(assemble()).status,pc:stable(state.pc),halted:state.halted,quorum:false,oneShadowOnly:true,physicalPromotion:false};
 const reg=routeResult.register;
 if(op==='STEP'){
   if(!['+','-'].includes(cmd.sign))return{status:'HOLD',reason:'INVALID_SIGN',physicalPromotion:false};
   if(cmd.global!==undefined||cmd.local!==undefined)return{status:'HOLD',reason:'STEP_USES_REGISTER_PC',physicalPromotion:false};
   const prev=state.pc[reg];const next=cmd.sign==='+'?prev%122+1:(prev+120)%122+1;
   state.pc[reg]=next;state.dispatchCount++;
   return{status:'SIMULATED_STEP',from:address(reg,prev),to:address(reg,next),sign:cmd.sign,physicalPromotion:false};
 }
 const at=routeResult.local??state.pc[reg],cell=assemble()[address(reg,at).global-1];
 state.dispatchCount++;
 if(op==='READ')return{status:'SIMULATED_READ',cell,physicalPromotion:false};
 if(op==='WITNESS')return{status:'SIMULATED_WITNESS',witness:cell.witness,cell,physicalPromotion:false};
 throw Error('UNHANDLED_OPCODE');
}
class Dispatcher{
 constructor(){this.state=initial();this.journal=[]}
 dispatch(command){
   const cmd=stable(command??{});
   const result=apply(this.state,cmd);
   const payload={seq:this.journal.length+1,previous:this.journal.at(-1)?.hash||'GENESIS',command:cmd,result:stable(result)};
   const entry={...payload,hash:hash(payload)};this.journal.push(entry);return result;
 }
 audit(){
   let previous='GENESIS';const replay=initial();
   for(let i=0;i<this.journal.length;i++){
     const entry=this.journal[i],{hash:provided,...payload}=entry;
     if(payload.seq!==i+1||payload.previous!==previous||provided!==hash(payload))return{status:'HOLD',reason:'JOURNAL_CHAIN'};
     const expected=apply(replay,payload.command);
     if(JSON.stringify(expected)!==JSON.stringify(payload.result))return{status:'HOLD',reason:'DETERMINISTIC_REPLAY'};
     previous=provided;
   }
   if(JSON.stringify(replay)!==JSON.stringify(this.state))return{status:'HOLD',reason:'LIVE_STATE_DIVERGENCE'};
   return{status:'PASS',entries:this.journal.length,head:previous,pc:stable(replay.pc),halted:replay.halted,checkpoint:stable(replay.checkpoint),physicalPromotion:false,quorum:false};
 }
 export(){return{schema:'JANE-B156-D-DISPATCH-TRACE-v1',journal:stable(this.journal),state:stable(this.state),audit:this.audit()}}
}
module.exports={REG,OPS,initial,route,apply,Dispatcher};
