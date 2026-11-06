'use strict';
/**
 * B179 independent fixed-template scanner.
 * Independently tokenizes characters / lines and computes issue-template
 * semantics; does not import or invoke B177's parser.
 * Error categories intentionally match B177 for differential comparisons.
 */
const crypto=require('node:crypto');
const {TEMPLATE}=require('./jane-b161-formic-agent.cjs');
const {fixtures}=require('./jane-b178-constraint-coverage.cjs');
const {parseTemplate:parseB177}=require('./jane-b177-semantic-template.cjs');
const EXPECTED=[['name','Bug report'],['about','Report a reproducible defect'],
 ['title','""'],['labels','bug'],['assignees','""']];
const TITLES=['Description','Steps to reproduce','Expected behavior','Actual behavior','Environment','Supporting evidence'];
const SCHEMA='JANE-B179-INDEPENDENT-PARSER-v1';
const hash=o=>crypto.createHash('sha256').update(JSON.stringify(o)).digest('hex');
function parseIndependent(source){
 if(typeof source!=='string'||Buffer.byteLength(source,'utf8')>8192||
  source.length===0||source.charCodeAt(0)===65279||source.charCodeAt(source.length-1)!==10||
  source.indexOf(String.fromCharCode(0))>=0||source.indexOf(String.fromCharCode(13))>=0)
   throw Error('ENCODING');
 // Character-scanning line tokenizer; no B177 split or field regex.
 const lines=[];let current='';
 for(let i=0;i<source.length;i++){
  const ch=source[i];
  if(ch==='\n'){lines.push(current);current=''}
  else current+=ch;
 }
 lines.push(current);
 if(lines[0]!=='---'||lines[6]!=='---'||lines[7]!=='')
  throw Error('FRONT_MATTER');
 const fields={};
 const names=new Set(EXPECTED.map(x=>x[0]));
 for(let row=1;row<=5;row++){
  const text=lines[row],colon=text.indexOf(':');
  if(colon<1||text[colon+1]!==' ')throw Error('FIELD_DUPLICATE_OR_UNKNOWN');
  const name=text.slice(0,colon),value=text.slice(colon+2);
  if(!names.has(name)||Object.hasOwn(fields,name)||
    [...name].some(ch=>ch<'a'||ch>'z'))throw Error('FIELD_DUPLICATE_OR_UNKNOWN');
  for(const c of value){
   if('&*!|>{}[]\\'.includes(c)||c===String.fromCharCode(96)||
      c==='$')throw Error('YAML_SPECIAL_OR_DYNAMIC');
  }
  if(value.includes('http'))throw Error('YAML_SPECIAL_OR_DYNAMIC');
  fields[name]=value;
 }
 for(const [name,value]of EXPECTED){
  if(!Object.hasOwn(fields,name))throw Error('MISSING_FIELD');
  if(fields[name]!==value)throw Error('FIELD_VALUE');
 }
 const contents=lines.slice(8),headings=[];
 for(const content of contents){
  const lower=content.toLowerCase(),trimmed=content.trimStart();
  if(lower.includes('javascript:')||lower.includes('data:')||
     content.includes('<%')||content.includes('{%')||
     trimmed.startsWith('![')||
     (trimmed.startsWith('[')&&trimmed.includes(']:'))||
     /<\/?[A-Za-z!]/.test(content))
     throw Error('ACTIVE_OR_LINKED_CONTENT');
  if(content.slice(0,3)==='## ')headings.push(content.slice(3));
 }
 if(headings.length!==TITLES.length||headings.some((v,i)=>v!==TITLES[i]))
  throw Error('HEADINGS');
 if(contents.some(x=>x.startsWith('#')&&!x.startsWith('## ')))throw Error('EXTRA_HEADING');
 const count=s=>contents.reduce((n,x)=>n+(x===s?1:0),0);
 if(count('Remove secrets, credentials, and personal information before attaching logs.')!==1)
  throw Error('REDACTION_WARNING');
 for(const step of ['1.','2.','3.'])if(count(step)!==1)throw Error('REPRODUCTION_STEPS');
 return{fields,headings,bytes:Buffer.byteLength(source,'utf8'),
  sha256:crypto.createHash('sha256').update(Buffer.from(source,'utf8')).digest('hex')};
}
function result(parser,text){
 try{return{accepted:true,semantic:parser(text),error:null}}
 catch(e){return{accepted:false,semantic:null,error:String(e.message)}}
}
function run({primary=parseB177,secondary=parseIndependent,cases=fixtures()}={}){
 const issues=[],rows=[];
 const baselineA=result(primary,TEMPLATE),baselineB=result(secondary,TEMPLATE);
 if(!baselineA.accepted||!baselineB.accepted||JSON.stringify(baselineA.semantic)!==JSON.stringify(baselineB.semantic))
  issues.push('CANONICAL_DIFFERENTIAL_DISAGREEMENT');
 const required=fixtures();
 const ids=new Set(required.map(c=>c.id)),seen=new Set();
 for(const c of cases){
  if(!c||typeof c.id!=='string'||seen.has(c.id)){issues.push('DUPLICATE_OR_MISSING_ID');continue}
  seen.add(c.id);
  const contract=required.find(x=>x.id===c.id);
  if(!contract||c.error!==contract.error||c.rule!==contract.rule||c.group!==contract.group)
   issues.push('CONTRACT_MISMATCH:'+c.id);
  let a,b;
  try{
   const input=c.make();
   if(input===TEMPLATE)throw Error('UNMUTATED_TEST');
   a=result(primary,input);b=result(secondary,input);
  }catch(e){a={accepted:true,error:'FIXTURE_ERROR'};b={accepted:true,error:String(e.message)}}
  const agree=!a.accepted&&!b.accepted&&a.error===b.error&&a.error===contract?.error;
  if(!agree)issues.push('PARSER_DISAGREEMENT:'+c.id+':'+a.error+'/'+b.error);
  rows.push({id:c.id,group:c.group,rule:c.rule,primaryError:a.error,independentError:b.error,
   expectedError:contract?.error??null,agreement:agree});
 }
 for(const id of ids)if(!seen.has(id))issues.push('MISSING_CASE:'+id);
 const report={schema:SCHEMA,status:issues.length?'HOLD':'INDEPENDENT_PARSER_AGREEMENT_NO_EXECUTION',
  canonicalAgreed:baselineA.accepted&&baselineB.accepted&&
   JSON.stringify(baselineA.semantic)===JSON.stringify(baselineB.semantic),
  required:required.length,observed:rows.length,rows,issues,
  authority:{mayCreatePR:false,mayRetry:false,mayMerge:false,mayWriteDefaultBranch:false},
  governance:{observerDepth:1,witnesses:['a1','b1','c1'],noQuorum:true,isaDefined:false,
   repoCodeExecuted:false,repoCIExecuted:false}};
 return{...report,attestationSha256:hash(report)};
}
function audit(r){
 if(r?.schema!==SCHEMA||r.status!=='INDEPENDENT_PARSER_AGREEMENT_NO_EXECUTION'||
 r.canonicalAgreed!==true||r.issues?.length!==0||r.observed!==r.required||
 r.rows?.some(x=>x.agreement!==true)||r.authority?.mayCreatePR!==false||
 r.authority?.mayMerge!==false||r.governance?.repoCodeExecuted!==false)
 return{status:'HOLD',reason:'BOUNDARY'};
 const {attestationSha256,...body}=r;
 return hash(body)===attestationSha256?{status:'PASS'}:{status:'HOLD',reason:'DIGEST'};
}
module.exports={SCHEMA,parseIndependent,run,audit};
