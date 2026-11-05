'use strict';
const crypto=require('node:crypto');
const {boundary,ownership}=require('./jane-b158-containment.cjs');
const hash=o=>crypto.createHash('sha256').update(JSON.stringify(o)).digest('hex');
const clone=o=>JSON.parse(JSON.stringify(o));
const WITNESSES=Object.freeze(['a1','b1','c1']);
function gate(from,to,sign){
 const b=boundary(from,to,sign);
 if(b.status!=='HOLD_SOURCE_WITNESS_REQUIRED'||!b.changesSource) return{status:'HOLD',reason:'NOT_A_CROSS_SOURCE_SEAM'};
 return{status:'BOUNDARY_OPEN_FOR_OBSERVATION',from:b.from,to:b.to,sign,departure:b.from.witness,arrival:b.to.witness,physicalPromotion:false};
}
function validateReport(g,report){
 if(!report||!['DEPARTURE','ARRIVAL'].includes(report.side))return'INVALID_SIDE';
 const expected=report.side==='DEPARTURE'?g.departure:g.arrival;
 if(report.witness!==expected)return'FOREIGN_WITNESS';
 if(typeof report.id!=='string'||!report.id.trim()||typeof report.boundaryId!=='string'||!report.boundaryId.trim())return'MISSING_IDENTIFIERS';
 if(typeof report.sawCrossing!=='boolean')return'MISSING_OR_UNDEFINED_OBSERVATION';
 if(typeof report.note!=='string')return'NOTE_NOT_TEXT';
 if(report.physicalPromotion!==false)return'PHYSICS_PROMOTION_FORBIDDEN';
 return null;
}
class BoundaryBook{
 constructor(){this.cases=new Map();this.logs={a1:[],b1:[],c1:[]};this.ids=new Set()}
 open({boundaryId,from,to,sign}){
  if(typeof boundaryId!=='string'||!boundaryId.trim()||this.cases.has(boundaryId))throw Error('INVALID_OR_DUPLICATE_BOUNDARY_ID');
  const g=gate(from,to,sign);if(g.status!=='BOUNDARY_OPEN_FOR_OBSERVATION')throw Error(g.reason);
  const record=Object.freeze({boundaryId,gate:g});
  this.cases.set(boundaryId,record);return clone(record);
 }
 append(report){
  const c=this.cases.get(report?.boundaryId);
  if(!c)throw Error('UNKNOWN_BOUNDARY');
  const reason=validateReport(c.gate,report);if(reason)throw Error(reason);
  if(this.ids.has(report.id))throw Error('DUPLICATE_REPORT_ID');
  const record=Object.freeze(clone(report));const log=this.logs[record.witness];
  const body={seq:log.length+1,previous:log.at(-1)?.hash||'GENESIS',record};
  const entry=Object.freeze({...body,hash:hash(body)});
  log.push(entry);this.ids.add(record.id);return clone(entry);
 }
 view(boundaryId){
  const c=this.cases.get(boundaryId);if(!c)return{status:'HOLD',reason:'UNKNOWN_BOUNDARY'};
  const reports=Object.values(this.logs).flatMap(log=>log.map(e=>e.record).filter(e=>e.boundaryId===boundaryId));
  const dep=reports.filter(x=>x.side==='DEPARTURE'),arr=reports.filter(x=>x.side==='ARRIVAL');
  const mismatch=dep.length&&arr.length&&dep.some(d=>arr.some(a=>d.sawCrossing!==a.sawCrossing));
  return{boundaryId,status:!dep.length||!arr.length?'UNMATCHED_HOLD':mismatch?'DISAGREEMENT_PRESERVED':'TWO_SIDES_RECORDED',
    from:c.gate.from.global,to:c.gate.to.global,departureCount:dep.length,arrivalCount:arr.length,
    reports:clone(reports),quorum:false,agreementRequired:false,physicalPromotion:false};
 }
 audit(){
  let count=0;const unique=new Set();
  for(const w of WITNESSES){let prev='GENESIS';
   for(let i=0;i<this.logs[w].length;i++){
    const e=this.logs[w][i],{hash:provided,...body}=e;
    const c=this.cases.get(body.record?.boundaryId);
    if(body.seq!==i+1||body.previous!==prev||provided!==hash(body)||!c||validateReport(c.gate,body.record)||body.record.witness!==w||unique.has(body.record.id))return{status:'HOLD',reason:'CHAIN_OR_PROVENANCE',source:w};
    prev=provided;unique.add(body.record.id);count++;
   }
  }
  if(unique.size!==this.ids.size)return{status:'HOLD',reason:'ID_REGISTRY_DIVERGED'};
  for(const c of this.cases.values())if(gate(c.gate.from.global,c.gate.to.global,c.gate.sign).status!=='BOUNDARY_OPEN_FOR_OBSERVATION')return{status:'HOLD',reason:'INVALID_GATE'};
  return{status:'PASS',cases:this.cases.size,independentReports:count,disagreements:[...this.cases.keys()].filter(k=>this.view(k).status==='DISAGREEMENT_PRESERVED').length,
    unmatched:[...this.cases.keys()].filter(k=>this.view(k).status==='UNMATCHED_HOLD').length,quorum:false,physicalPromotion:false};
 }
 export(){return{schema:'JANE-B159-PAIRWISE-BOUNDARY-OBSERVATIONS-v1',cases:[...this.cases.values()].map(clone),logs:clone(this.logs),audit:this.audit()}}
}
module.exports={WITNESSES,gate,validateReport,BoundaryBook};
