'use strict';
const BOX=Object.freeze([1,2,4,6,8,12,12,8,6,2,1]);
const TOR=Object.freeze([1,3,6,9,11,11,9,6,3,1]);
const BRACES=Object.freeze(['H','O','N']);
const WITNESSES=Object.freeze(['a1','b1','c1']);
function sum(xs){return xs.reduce((a,b)=>a+b,0)}
function assertCounts(){if(sum(BOX)!==62||sum(TOR)!==60||62+60!==122)throw Error('CELL_INVARIANT_FAILURE');return true}
function build(brace){
 assertCounts();
 const ordinal=BRACES.indexOf(brace);if(ordinal<0)throw Error('UNKNOWN_BRACE');
 const all=[];let local=0;
 for(const [kind,counts]of [['Box62',BOX],['Toroid60',TOR]]){
  for(let layer=0;layer<counts.length;layer++){
   for(let position=0;position<counts[layer];position++){
    local++;
    all.push({brace,witness:WITNESSES[ordinal],local,global:ordinal*122+local,kind,layer:layer+1,slot:position+1,layerPopulation:counts[layer],signedOptions:['-','+'],physicalPromotion:false});
   }
  }
 }
 return all;
}
function allCells(){return BRACES.flatMap(build)}
function locate(brace,local){
 if(!Number.isInteger(local)||local<1||local>122)throw Error('OUT_OF_BOUNDS_LOCAL_CELL');
 return build(brace)[local-1];
}
function traverse(brace,from,to,sign){
 if(!['-','+'].includes(sign))return{status:'HOLD',reason:'INVALID_SIGN'};
 if(!Number.isInteger(from)||!Number.isInteger(to)||from<1||from>122||to<1||to>122)return{status:'HOLD',reason:'CELL_OUT_OF_RANGE'};
 if(sign==='+'&&to!==from%122+1)return{status:'HOLD',reason:'NON_FORWARD_STEP'};
 if(sign==='-'&&to!==(from+120)%122+1)return{status:'HOLD',reason:'NON_REVERSE_STEP'};
 const end=locate(brace,to),start=locate(brace,from);
 return{status:'SIMULATED_STEP',brace,from,to,fromKind:start.kind,toKind:end.kind,sign,physicalPromotion:false};
}
function audit(d){
 const errors=[];if(d?.schema!=='JANE-B153-HON-BRACED-122-v1')errors.push('SCHEMA');
 if(JSON.stringify(d?.cage?.counts)!==JSON.stringify(BOX)||d.cage.positions!==62)errors.push('BOX62');
 if(JSON.stringify(d?.torus?.counts)!==JSON.stringify(TOR)||d.torus.positions!==60)errors.push('TOROID60');
 if(d?.cellsPerBrace!==122||d?.totalCells!==366)errors.push('COUNTS');
 if(JSON.stringify(d?.scouts?.map(x=>x.brace))!==JSON.stringify(BRACES)||JSON.stringify(d?.scouts?.map(x=>x.witness))!==JSON.stringify(WITNESSES))errors.push('BRACES');
 if(d?.scouts?.some((s,i)=>s.globalStart!==i*122+1||s.globalEnd!==(i+1)*122))errors.push('GLOBAL_BOUNDS');
 if(d?.firstShadow?.onlyFirstPair!==true||d.firstShadow.net!==0||d.firstShadow.foldedPositions!==1)errors.push('SHADOW');
 if(d?.signedDirections?.ingress!=='-'||d.signedDirections.egress!=='+'||d.signedDirections.notAdditionalCells!==true)errors.push('POLARITY');
 if(d?.physicalPromotion!==false||d?.metricStatus!=='HOLD'||d?.releaseStatus!=='SIMULATION_ONLY')errors.push('PHYSICS_GATE');
 return{status:errors.length?'HOLD':'STRUCTURAL_PASS',errors,braces:3,boxCells:62,torusCells:60,perBrace:122,total:366};
}
module.exports={BOX,TOR,BRACES,WITNESSES,sum,build,allCells,locate,traverse,audit};
