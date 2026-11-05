'use strict';
const crypto=require('node:crypto');
const {build}=require('./jane-b153-hon-braces.cjs');
const REGISTERS=Object.freeze({a:Object.freeze({brace:'H',witness:'a1',start:1,end:122}),b:Object.freeze({brace:'O',witness:'b1',start:123,end:244}),c:Object.freeze({brace:'N',witness:'c1',start:245,end:366})});
const OPCODES=Object.freeze(['ADDR','READ','STEP','ASSEMBLE','WITNESS','CHECK']);
const digest=v=>crypto.createHash('sha256').update(JSON.stringify(v)).digest('hex');
const validReg=r=>Object.hasOwn(REGISTERS,r);
const validCell=i=>Number.isInteger(i)&&i>=1&&i<=122;
function address(reg,local){if(!validReg(reg)||!validCell(local))throw Error('INVALID_REGISTER_OR_LOCAL');const r=REGISTERS[reg];return Object.freeze({register:reg,brace:r.brace,witness:r.witness,local,global:r.start+local-1})}
function decode(global){if(!Number.isInteger(global)||global<1||global>366)throw Error('INVALID_GLOBAL_ADDRESS');const idx=Math.floor((global-1)/122),reg=['a','b','c'][idx];return address(reg,(global-1)%122+1)}
function assemble(){const d=[];for(const r of ['a','b','c'])for(const cell of build(REGISTERS[r].brace))d.push(Object.freeze({...address(r,cell.local),kind:cell.kind,layer:cell.layer,slot:cell.slot,physicalPromotion:false}));return Object.freeze(d)}
function assertComposition(d){if(!Array.isArray(d)||d.length!==366)return{status:'HOLD',reason:'COMPOSITION_SIZE'};for(let i=0;i<366;i++){const expect=decode(i+1),row=d[i];if(!row||row.global!==expect.global||row.local!==expect.local||row.register!==expect.register||row.brace!==expect.brace||row.physicalPromotion!==false)return{status:'HOLD',reason:'COMPOSITION_IDENTITY',index:i}}return{status:'PASS',length:366,registries:3,independentD:false,physicalPromotion:false}}
class Machine{
 constructor(){this.pc={a:1,b:1,c:1};this.journal=[];this.d=assemble();this.lastRead=null}
 append({opcode,args,result}){const body={seq:this.journal.length+1,previous:this.journal.at(-1)?.hash||'GENESIS',opcode,args,result};const entry=Object.freeze({...body,hash:digest(body)});this.journal.push(entry);return entry}
 execute(opcode,args={}){
  if(!OPCODES.includes(opcode))return{status:'HOLD',reason:'INVALID_OPCODE'};
  let result;
  try{
   if(opcode==='ADDR')result=decode(args.global);
   if(opcode==='READ'){const reg=args.register,at=args.local??this.pc[reg];const addr=address(reg,at);result=this.d[addr.global-1];this.lastRead=result}
   if(opcode==='STEP'){if(!validReg(args.register)||!['+','-'].includes(args.sign))throw Error('INVALID_STEP');const r=args.register,from=this.pc[r],to=args.sign==='+'?from%122+1:(from+120)%122+1;this.pc[r]=to;result={...address(r,to),from,sign:args.sign,status:'SIMULATED_STEP',physicalPromotion:false}}
   if(opcode==='ASSEMBLE')result=assertComposition(this.d);
   if(opcode==='WITNESS'){if(!validReg(args.register))throw Error('INVALID_WITNESS');const r=args.register;result={status:'OBSERVED_SIMULATION',witness:REGISTERS[r].witness,register:r,pointer:this.pc[r],global:address(r,this.pc[r]).global,physicalPromotion:false}}
   if(opcode==='CHECK')result={...assertComposition(this.d),pointerBounds:Object.values(this.pc).every(validCell),shadowPairs:1,quorum:false};
  }catch(err){return{status:'HOLD',reason:err.message}}
  this.append({opcode,args:structuredClone(args),result:structuredClone(result)});
  return result;
 }
 replayAudit(){
  let previous='GENESIS';
  for(let i=0;i<this.journal.length;i++){const e=this.journal[i],{hash,...body}=e;if(body.seq!==i+1||body.previous!==previous||digest(body)!==hash) return{status:'HOLD',reason:'JOURNAL_MISMATCH'};previous=hash}
  return{status:'PASS',entries:this.journal.length,head:previous,quorum:false,physicalPromotion:false};
 }
}
module.exports={REGISTERS,OPCODES,address,decode,assemble,assertComposition,Machine};
