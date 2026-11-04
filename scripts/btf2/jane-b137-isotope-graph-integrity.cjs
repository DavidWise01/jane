'use strict';
// B137: bounded isotope-composition registry and verified-structure graph audit.
// CIAAW rows are representative *natural abundance* members, not all nuclides.
// Status of each isotope remains unclassified unless evaluated nuclear data added.
const CIAAW='https://ciaaw.org/isotopic-abundances.htm';
const KR='https://www.ciaaw.org/krypton.htm';
const IAEA='https://nucleus.iaea.org/Pages/livechart-of-nuclides-av.aspx';
const ELEMENTS=Object.freeze([
 [1,'H',[1,2]],[2,'He',[3,4]],[3,'Li',[6,7]],
 [4,'Be',[9]],[5,'B',[10,11]],[6,'C',[12,13]],
 [7,'N',[14,15]],[8,'O',[16,17,18]],[9,'F',[19]],
 [10,'Ne',[20,21,22]],[36,'Kr',[78,80,82,83,84,86]]
].map(([Z,symbol,masses])=>Object.freeze({Z,symbol,masses:Object.freeze(masses),abundanceSource:symbol==='Kr'?KR:CIAAW})));
const natural=Object.freeze(ELEMENTS.flatMap(e=>e.masses.map(A=>Object.freeze({
 key:e.symbol+'-'+A,Z:e.Z,A,N:A-e.Z,kind:'natural_isotopic_composition',nuclearStatus:'NOT_EVALUATED_HERE',source:e.abundanceSource
}))));
const supplementary=Object.freeze([
 Object.freeze({key:'Kr-81',Z:36,A:81,N:45,kind:'trace_radioisotope',nuclearStatus:'RADIOACTIVE',source:IAEA}),
 Object.freeze({key:'Kr-85',Z:36,A:85,N:49,kind:'trace_radioisotope',nuclearStatus:'RADIOACTIVE',source:IAEA})
]);
const registry=new Map([...natural,...supplementary].map(n=>[n.key,n]));
function classifyScope({Z,naturalMasses}){
 const e=ELEMENTS.find(x=>x.Z===Z);
 if(!e) return {scope:'NOT_DECLARED',naturalCoverage:null,nuclearCensusCoverage:null};
 const expected=new Set(e.masses),actual=new Set(naturalMasses);
 const extras=[...actual].filter(a=>!expected.has(a));
 const missing=[...expected].filter(a=>!actual.has(a));
 return {scope:'CIAAW_NATURAL_COMPOSITION_ONLY',expected:expected.size,recorded:actual.size,missing,extras,
   naturalCoverage:expected.size?100*(expected.size-missing.length)/expected.size:null,
   nuclearCensusCoverage:null};
}
function entry(key){return registry.get(key)||null;}
function validateNuclide(n){return !!(n&&Number.isInteger(n.Z)&&Number.isInteger(n.A)&&n.Z>=0&&n.A>=n.Z&&n.N===n.A-n.Z&&n.key&&n.source);}
function balanceReaction(reaction,nuclides){
 if(!reaction||!Array.isArray(reaction.inputs)||!Array.isArray(reaction.outputs)||!reaction.inputs.length||!reaction.outputs.length)return {status:'UNKNOWN',reason:'MISSING_REACTION_DETAILS'};
 const total=keys=>keys.reduce((a,k)=>{
  const n=nuclides[k];if(!n)throw Error('UNKNOWN_NUCLIDE:'+k);
  return {A:a.A+n.A,Z:a.Z+n.Z};
 },{A:0,Z:0});
 try{
  const before=total(reaction.inputs),after=total(reaction.outputs);
  if(before.A!==after.A||before.Z!==after.Z)return{status:'REJECT',reason:'NUCLEON_OR_CHARGE_MISMATCH'};
  if(!reaction.evidence||!/^https:\/\//.test(reaction.evidence))return {status:'HOLD',reason:'UNSOURCED_REACTION'};
  return {status:'ACCOUNTING_PASS',reason:'EVIDENCE_LINK_PRESENT_NOT_INDEPENDENTLY_VERIFIED'};
 }catch(e){return {status:'HOLD',reason:'UNRESOLVED_REACTION_PARTICIPANT'};}
}
function inheritedEdges(){
 const b128=require('./jane-b128-elemental-growth.cjs');
 return b128.PATHS.map(p=>({id:p.id,inputs:p.inputs,outputs:p.outputs,evidence:p.evidence,accounting:balanceReaction(p,b128.NUCLIDES)}));
}
function audit(){
 const keys=new Set();for(const n of registry.values()){if(!validateNuclide(n)||keys.has(n.key))throw Error('Invalid or duplicate nuclide');keys.add(n.key);}
 const scopes=ELEMENTS.map(e=>({element:e.symbol,...classifyScope({Z:e.Z,naturalMasses:natural.filter(n=>n.Z===e.Z).map(n=>n.A)})}));
 if(scopes.some(s=>s.missing.length||s.extras.length||s.nuclearCensusCoverage!==null))throw Error('Bad declared scope');
 const edges=inheritedEdges();if(edges.length!==5||edges.some(x=>x.accounting.status!=='ACCOUNTING_PASS'))throw Error('Prior graph accounting mismatch');
 return {naturalRows:natural.length,supplementaryRows:supplementary.length,declaredElements:ELEMENTS.length,
  naturalCompositionalScopeComplete:true,allKnownNuclidesComplete:false,allKnownNuclideCoveragePercent:null,
  inheritedDocumentedEdges:edges.length,inventedEdges:0,scopes,edges};
}
module.exports={CIAAW,KR,IAEA,ELEMENTS,natural,supplementary,registry,classifyScope,entry,validateNuclide,balanceReaction,inheritedEdges,audit};
