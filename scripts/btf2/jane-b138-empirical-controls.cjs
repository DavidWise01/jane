'use strict';
// B138 compares fixed, attributed reference values against test assertions.
// It does not make external measurements or validate citation contents.
const crypto=require('node:crypto');
const REFERENCES=Object.freeze({
 'H3_HALF_LIFE':Object.freeze({kind:'numeric',value:12.32,unit:'year',tolerance:0.02,source:'https://www-nds.iaea.org/publications/indc/indc-ccp-0419.pdf',sourceDetail:'IAEA recommended tritium half-life 12.32 +/- 0.02 years'}),
 'DT_FUSION_Q':Object.freeze({kind:'numeric',value:17.60,unit:'MeV',tolerance:0.05,source:'https://www-pub.iaea.org/MTCD/Publications/PDF/FusionOutlook2023_web.pdf',sourceDetail:'IAEA D-T fusion available energy 17.60 MeV'}),
 'KR84_STATUS':Object.freeze({kind:'categorical',value:'STABLE',unit:'nuclear_status',source:'https://pubchem.ncbi.nlm.nih.gov/element/36',sourceDetail:'PubChem isotope record Krypton-84 stable'})
});
function evaluate(candidate){
 if(!candidate||!candidate.id||!candidate.claim||!candidate.referenceId||!candidate.source)throw Error('Candidate needs ID, claim, reference and cited source');
 const ref=REFERENCES[candidate.referenceId];
 if(!ref)return {id:candidate.id,result:'HOLD',reason:'UNKNOWN_REFERENCE',referenceId:candidate.referenceId};
 if(candidate.unit!==ref.unit)return {id:candidate.id,result:'HOLD',reason:'INCOMPATIBLE_UNIT',referenceId:candidate.referenceId};
 if(ref.kind==='numeric'){
  if(typeof candidate.value!=='number'||!Number.isFinite(candidate.value))return {id:candidate.id,result:'HOLD',reason:'INVALID_NUMBER',referenceId:candidate.referenceId};
  const diff=Math.abs(candidate.value-ref.value);
  return {id:candidate.id,result:diff<=ref.tolerance?'PASS':'REJECT',reason:diff<=ref.tolerance?'REFERENCE_MATCH':'REFERENCE_CONTRADICTION',difference:diff,referenceId:candidate.referenceId};
 }
 if(typeof candidate.value!=='string')return {id:candidate.id,result:'HOLD',reason:'INVALID_CATEGORY',referenceId:candidate.referenceId};
 return {id:candidate.id,result:candidate.value===ref.value?'PASS':'REJECT',reason:candidate.value===ref.value?'REFERENCE_MATCH':'REFERENCE_CONTRADICTION',referenceId:candidate.referenceId};
}
function frozen(x){if(x&&typeof x==='object'&&!Object.isFrozen(x)){Object.values(x).forEach(frozen);Object.freeze(x);}return x;}
const digest=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
class EvidenceJournal{
 constructor(){this.entries=[];}
 submit(candidate){
  const verdict=evaluate(candidate);
  if(this.entries.some(e=>e.candidate.id===candidate.id))throw Error('Duplicate claim ID');
  const body={ordinal:this.entries.length+1,previous:this.entries.at(-1)?.hash||'GENESIS',candidate:frozen({...candidate}),verdict:frozen(verdict)};
  const entry=frozen({...body,hash:digest(body)});this.entries.push(entry);return verdict;
 }
 audit(){let previous='GENESIS';for(const [i,e] of this.entries.entries()){const {hash,...body}=e;if(e.ordinal!==i+1||e.previous!==previous||digest(body)!==hash)throw Error('Tampered journal');previous=hash;}
 return {claims:this.entries.length,pass:this.entries.filter(e=>e.verdict.result==='PASS').length,reject:this.entries.filter(e=>e.verdict.result==='REJECT').length,hold:this.entries.filter(e=>e.verdict.result==='HOLD').length,chainVerified:true};}
}
module.exports={REFERENCES,evaluate,EvidenceJournal};
