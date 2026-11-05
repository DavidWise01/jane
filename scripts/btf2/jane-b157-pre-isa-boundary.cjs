'use strict';
const {build,BOX,TOR}=require('./jane-b153-hon-braces.cjs');
const REG=Object.freeze({a:Object.freeze({brace:'H',witness:'a1',offset:0}),b:Object.freeze({brace:'O',witness:'b1',offset:122}),c:Object.freeze({brace:'N',witness:'c1',offset:244})});
const ORDER=Object.freeze(['a','b','c']);const sum=a=>a.reduce((s,n)=>s+n,0);
function sources(){return Object.fromEntries(ORDER.map(r=>[r,build(REG[r].brace).map(cell=>Object.freeze({register:r,brace:cell.brace,witness:cell.witness,local:cell.local,global:cell.global,kind:cell.kind,layer:cell.layer,position:cell.slot}))]));}
function assemble(src=sources()){return Object.freeze(ORDER.flatMap(r=>src[r]||[]));}
function address(reg,local){if(!REG[reg]||!Number.isInteger(local)||local<1||local>122)return null;return{register:reg,brace:REG[reg].brace,witness:REG[reg].witness,local,global:REG[reg].offset+local};}
function decode(global){if(!Number.isInteger(global)||global<1||global>366)return null;const k=Math.floor((global-1)/122),r=ORDER[k];return address(r,(global-1)%122+1);}
function observe(reg,local){const a=address(reg,local);if(!a)return{status:'HOLD',reason:'ADDRESS_OUT_OF_BOUNDS'};const c=sources()[reg][local-1];return{status:'OBSERVED_SYMBOLIC_CELL',cell:c,physicalPromotion:false};}
function audit(src=sources()){
 const errors=[],flat=assemble(src);
 if(sum(BOX)!==62||sum(TOR)!==60)errors.push('LAYER_TOTAL');
 for(const r of ORDER){if(!Array.isArray(src[r])||src[r].length!==122){errors.push('SOURCE_LENGTH_'+r);continue}
   for(let i=0;i<122;i++){const expected=address(r,i+1),c=src[r][i],kind=i<62?'Box62':'Toroid60';
     if(!c||c.register!==r||c.global!==expected.global||c.local!==i+1||c.brace!==expected.brace||c.witness!==expected.witness||c.kind!==kind) {errors.push('SOURCE_MUTATION_'+r+'_'+(i+1));break}
   }
 }
 if(flat.length!==366||new Set(flat.map(c=>c.global)).size!==366||flat.some((c,i)=>c.global!==i+1))errors.push('DERIVED_VIEW_INCOMPLETE');
 return{status:errors.length?'HOLD':'STRUCTURAL_PASS',errors,sourceRegisters:3,cellsPerSource:122,derivedCells:366,additionalCellsInD:0,isaDefined:false,physicalPromotion:false,quorum:false};
}
function next(reg,local,sign){if(!address(reg,local)||!['+','-'].includes(sign))return{status:'HOLD',reason:'INVALID_TRANSITION'};const to=sign==='+'?local%122+1:(local+120)%122+1;return{status:'SIMULATED_ADDRESS_TRANSITION',from:address(reg,local),to:address(reg,to),sign,physicalPromotion:false};}
module.exports={REG,ORDER,sources,assemble,address,decode,observe,audit,next};
