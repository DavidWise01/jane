'use strict';
const crypto=require('node:crypto');
const {BRACES,build,traverse}=require('./jane-b153-hon-braces.cjs');
const hash=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
function walk(brace,sign,start=1){
 if(!BRACES.includes(brace)||!['+','-'].includes(sign)||!Number.isInteger(start)||start<1||start>122)throw Error('INVALID_WALK_PARAMETERS');
 let local=start,previous='GENESIS';
 const records=[],departures=[],arrivals=[];
 for(let i=0;i<122;i++){
  const next=sign==='+'?local%122+1:(local+120)%122+1;
  const checked=traverse(brace,local,next,sign);
  if(checked.status!=='SIMULATED_STEP')throw Error('FAILED_SEAM_OR_DIRECTION');
  departures.push(local);arrivals.push(next);
  const payload={index:i+1,brace,witness:BRACES.indexOf(brace)===0?'a1':BRACES.indexOf(brace)===1?'b1':'c1',sign,from:local,to:next,fromKind:checked.fromKind,toKind:checked.toKind,previous,physicalPromotion:false};
  const record=Object.freeze({...payload,hash:hash(payload)});records.push(record);previous=record.hash;local=next;
 }
 return{brace,sign,start,end:local,departures,arrivals,records,head:previous};
}
function audit(w){
 if(!w||!BRACES.includes(w.brace)||!['+','-'].includes(w.sign)||!Number.isInteger(w.start)||w.start<1||w.start>122||!Array.isArray(w.records))return{status:'HOLD',reason:'INVALID_WALK'};
 let previous='GENESIS',position=w.start;
 const departed=new Set(),arrived=new Set();
 for(let i=0;i<w.records.length;i++){
  const r=w.records[i],{hash:actual,...payload}=r;
  if(payload.index!==i+1||payload.brace!==w.brace||payload.sign!==w.sign||payload.from!==position||payload.previous!==previous||payload.physicalPromotion!==false||hash(payload)!==actual)return{status:'HOLD',reason:'CHAIN_OR_SEQUENCE'};
  const expected=traverse(w.brace,position,payload.to,w.sign);
  if(expected.status!=='SIMULATED_STEP'||expected.fromKind!==payload.fromKind||expected.toKind!==payload.toKind)return{status:'HOLD',reason:'INVALID_TRANSITION'};
  departed.add(position);arrived.add(payload.to);position=payload.to;previous=actual;
 }
 if(w.records.length!==122||w.end!==w.start||position!==w.start||departed.size!==122||arrived.size!==122||w.head!==previous||JSON.stringify([...departed])!==JSON.stringify(w.departures)||JSON.stringify([...arrived])!==JSON.stringify(w.arrivals))return{status:'HOLD',reason:'INCOMPLETE_OR_DUPLICATE_COVERAGE'};
 return{status:'PASS',brace:w.brace,sign:w.sign,steps:122,uniqueDepartures:122,uniqueArrivals:122,returnHome:true,boxEntries:w.records.filter(x=>x.toKind==='Box62').length,toroidEntries:w.records.filter(x=>x.toKind==='Toroid60').length,physicalPromotion:false};
}
function roundTrip(brace,start=1){
 const forward=walk(brace,'+',start),reverse=walk(brace,'-',start);
 const f=audit(forward),r=audit(reverse);
 const reversePath=[...forward.records].reverse().map(x=>[x.to,x.from]),reverseActual=reverse.records.map(x=>[x.from,x.to]);
 const mirrored=JSON.stringify(reversePath)===JSON.stringify(reverseActual);
 const status=f.status==='PASS'&&r.status==='PASS'&&mirrored?'PASS':'HOLD';
 return{brace,start,status,forward,reverse,invariants:{forward:f,reverse:r,mirror:mirrored,steps:244,returnHome:status==='PASS',physicalPromotion:false}};
}
function all(){return BRACES.map(b=>roundTrip(b))}
module.exports={walk,audit,roundTrip,all};
