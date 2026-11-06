'use strict';
/**
 * B180 — deterministic bounded adversarial parser differential.
 * Reproducible PRNG, fixed mutation operators, no network, no repo execution.
 * A mutation is required to be rejected by both parsers with the expected
 * category; any divergence, acceptance, or missing case is HOLD.
 */
const crypto=require('node:crypto');
const {TEMPLATE}=require('./jane-b161-formic-agent.cjs');
const {parseTemplate:primary}=require('./jane-b177-semantic-template.cjs');
const {parseIndependent:secondary}=require('./jane-b179-independent-parser.cjs');
const SCHEMA='JANE-B180-DETERMINISTIC-FUZZ-v1';
const SEED=0x180b179;
const ROUNDS=20;
const MAX_INPUT_BYTES=9216;
const MAX_COUNTEREXAMPLES=12;
const FIELDS=[['name','Bug report'],['about','Report a reproducible defect'],
 ['title','""'],['labels','bug'],['assignees','""']];
const HEADINGS=['Description','Steps to reproduce','Expected behavior',
 'Actual behavior','Environment','Supporting evidence'];
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const digest=o=>sha(JSON.stringify(o));
function random(seed){
 let x=seed>>>0;
 return()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return x>>>0};
}
function replaceOnce(text,from,to){
 if(!text.includes(from))throw Error('MUTATION_ANCHOR_MISSING');
 return text.replace(from,to);
}
function operations(){
 return[
  {id:'field-value',error:'FIELD_VALUE',make:(r,i)=>{
   const [k,v]=FIELDS[r()%FIELDS.length];
   return replaceOnce(TEMPLATE,k+': '+v,k+': '+v+' fuzz'+i)}},
  {id:'field-remove',error:'FRONT_MATTER',make:r=>{
   const [k,v]=FIELDS[r()%FIELDS.length];
   return replaceOnce(TEMPLATE,k+': '+v+'\n','')}},
  {id:'field-duplicate',error:'FRONT_MATTER',make:r=>{
   const [k,v]=FIELDS[r()%FIELDS.length];
   return replaceOnce(TEMPLATE,k+': '+v,k+': '+v+'\n'+k+': '+v)}},
  {id:'field-unknown',error:'FIELD_DUPLICATE_OR_UNKNOWN',make:(r,i)=>{
   return replaceOnce(TEMPLATE,'labels: bug','unknown'+i+': bug')}},
  {id:'field-yaml-alias',error:'YAML_SPECIAL_OR_DYNAMIC',make:(r,i)=>{
   const [k]=FIELDS[r()%FIELDS.length];return replaceOnce(TEMPLATE,k+': ',k+': &fuzz'+i)}},
  {id:'field-interpolation',error:'YAML_SPECIAL_OR_DYNAMIC',make:(r,i)=>{
   const [k]=FIELDS[r()%FIELDS.length];return replaceOnce(TEMPLATE,k+': ',k+': $'+'{fuzz'+i+'}')}},
  {id:'heading-altered',error:'HEADINGS',make:(r,i)=>{
   const name=HEADINGS[r()%HEADINGS.length];return replaceOnce(TEMPLATE,'## '+name,'## Alternate '+i)}},
  {id:'heading-removed',error:'HEADINGS',make:r=>{
   const name=HEADINGS[r()%HEADINGS.length];return replaceOnce(TEMPLATE,'## '+name+'\n','')}},
  {id:'heading-root',error:'HEADINGS',make:r=>{
   const name=HEADINGS[r()%HEADINGS.length];return replaceOnce(TEMPLATE,'## '+name,'# '+name)}},
  {id:'body-html',error:'ACTIVE_OR_LINKED_CONTENT',make:(r,i)=>{
   const tag=['script','iframe','style','svg'][r()%4];
   return replaceOnce(TEMPLATE,'Describe the problem.','<'+tag+'>x'+i+'</'+tag+'>')}},
  {id:'body-javascript',error:'ACTIVE_OR_LINKED_CONTENT',make:(r,i)=>
   replaceOnce(TEMPLATE,'Describe the problem.','javascript:alert('+i+')')},
  {id:'body-data',error:'ACTIVE_OR_LINKED_CONTENT',make:(r,i)=>
   replaceOnce(TEMPLATE,'Describe the problem.','data:text/html,fuzz'+i)},
  {id:'body-reference',error:'ACTIVE_OR_LINKED_CONTENT',make:(r,i)=>
   replaceOnce(TEMPLATE,'Describe the problem.','[link'+i+']: https://invalid.example')},
  {id:'body-image',error:'ACTIVE_OR_LINKED_CONTENT',make:(r,i)=>
   replaceOnce(TEMPLATE,'Describe the problem.','![img'+i+'](https://invalid.example)')},
  {id:'redaction-removed',error:'REDACTION_WARNING',make:(r,i)=>
   replaceOnce(TEMPLATE,'Remove secrets, credentials, and personal information before attaching logs.','Redaction missing '+i)},
  {id:'repro-step',error:'REPRODUCTION_STEPS',make:r=>{
   const n=1+(r()%3);return replaceOnce(TEMPLATE,'\n'+n+'.\n','\nstep-'+n+'\n')}},
  {id:'encoding-crlf',error:'ENCODING',make:()=>TEMPLATE.replace(/\n/g,'\r\n')},
  {id:'encoding-nul',error:'ENCODING',make:(r,i)=>TEMPLATE+String.fromCharCode(0)+i},
  {id:'encoding-bom',error:'ENCODING',make:()=>String.fromCharCode(65279)+TEMPLATE},
  {id:'encoding-no-newline',error:'ENCODING',make:()=>TEMPLATE.slice(0,-1)}
 ];
}
function decision(parser,value){
 try{return{accept:true,semantic:parser(value),error:null}}
 catch(e){return{accept:false,semantic:null,error:String(e.message)}}
}
function reproducibleMutations({seed=SEED,rounds=ROUNDS}={}){
 if(!Number.isInteger(seed)||seed<0||seed>0xffffffff||!Number.isInteger(rounds)||rounds<1||rounds>64)
  throw Error('INVALID_FUZZ_PARAMETERS');
 const r=random(seed),list=[];
 for(const op of operations())for(let i=0;i<rounds;i++){
  const value=op.make(r,i);
  if(typeof value!=='string'||value===TEMPLATE||Buffer.byteLength(value,'utf8')>MAX_INPUT_BYTES)
   throw Error('INVALID_GENERATED_INPUT:'+op.id);
  list.push({id:op.id+'-'+i,operator:op.id,expectedError:op.error,value});
 }
 return list;
}
function run({seed=SEED,rounds=ROUNDS,first=primary,second=secondary,mutations=null}={}){
 const issues=[],rows=[],counterexamples=[];
 const aa=decision(first,TEMPLATE),bb=decision(second,TEMPLATE);
 const canonical=aa.accept&&bb.accept&&JSON.stringify(aa.semantic)===JSON.stringify(bb.semantic);
 if(!canonical)issues.push('CANONICAL_DISAGREEMENT');
 const expectedOps=operations();
 const generated=reproducibleMutations({seed,rounds});
 const cases=mutations??generated;
 if(!Array.isArray(cases)||cases.length!==generated.length)
  issues.push('MUTATION_COUNT_MISMATCH');
 const reference=new Map(generated.map(x=>[x.id,x]));
 const seen=new Set();
 for(const item of cases){
  if(!item||typeof item.id!=='string'||seen.has(item.id)){issues.push('INVALID_OR_DUPLICATE_CASE');continue}
  seen.add(item.id);
  const contract=reference.get(item.id);
  if(!contract||contract.expectedError!==item.expectedError||contract.value!==item.value)
   issues.push('MUTATION_CONTRACT_MISMATCH:'+item.id);
  if(typeof item.value!=='string'||item.value===TEMPLATE||
      Buffer.byteLength(item.value,'utf8')>MAX_INPUT_BYTES){
   issues.push('UNSAFE_MUTATION_INPUT:'+item.id);continue
  }
  const a=decision(first,item.value),b=decision(second,item.value);
  const correct=!a.accept&&!b.accept&&a.error===b.error&&a.error===contract?.expectedError;
  if(!correct){
   issues.push('DIFFERENTIAL_HOLD:'+item.id);
   if(counterexamples.length<MAX_COUNTEREXAMPLES){
    counterexamples.push({id:item.id,operator:item.operator,expectedError:contract?.expectedError??null,
     primary:{accepted:a.accept,error:a.error},independent:{accepted:b.accept,error:b.error},
     inputSha256:sha(Buffer.from(item.value,'utf8')),inputBytes:Buffer.byteLength(item.value,'utf8'),
     // Short literal preview is retained for reproducibility; inputs are local generated strings only.
     inputPreview:item.value.slice(0,320)});
   }
  }
  rows.push({id:item.id,operator:item.operator,expectedError:contract?.expectedError??null,
   primaryError:a.error,independentError:b.error,agreement:correct});
 }
 for(const item of generated)if(!seen.has(item.id))issues.push('MISSING_CASE:'+item.id);
 const counts={expected:generated.length,observed:rows.length,agreed:rows.filter(x=>x.agreement).length,
  disagreements:rows.filter(x=>!x.agreement).length,operators:expectedOps.length};
 const evidence={schema:SCHEMA,status:issues.length?'HOLD':'DETERMINISTIC_FUZZ_AGREEMENT_NO_EXECUTION',
  seed,rounds,canonicalAgreed:canonical,counts,rows,issues,counterexamples,
  inputDigest:sha(generated.map(x=>x.id+':'+sha(Buffer.from(x.value,'utf8'))).join('|')),
  governance:{witnesses:['a1','b1','c1'],observerDepth:1,noQuorum:true,isaDefined:false,
   repositoryCodeExecuted:false,repositoryCIExecuted:false},
  authority:{mayCreatePR:false,mayRetry:false,mayMerge:false,mayWriteDefaultBranch:false}};
 return{...evidence,attestationSha256:digest(evidence)};
}
function audit(record){
 if(record?.schema!==SCHEMA||record.status!=='DETERMINISTIC_FUZZ_AGREEMENT_NO_EXECUTION'||
   record.canonicalAgreed!==true||record.issues?.length!==0||record.counterexamples?.length!==0||
   record.counts?.expected!==record.counts?.observed||record.counts?.agreed!==record.counts?.expected||
   record.governance?.repositoryCodeExecuted!==false||record.authority?.mayCreatePR!==false||
   record.authority?.mayMerge!==false)return{status:'HOLD',reason:'BOUNDARY'};
 const {attestationSha256,...body}=record;
 return digest(body)===attestationSha256?{status:'PASS'}:{status:'HOLD',reason:'ATTESTATION'};
}
module.exports={SCHEMA,SEED,ROUNDS,operations,reproducibleMutations,decision,run,audit};
