'use strict';
const crypto=require('node:crypto');
const {TEMPLATE}=require('./jane-b161-formic-agent.cjs');
const {parseTemplate}=require('./jane-b177-semantic-template.cjs');
const SCHEMA='JANE-B178-CONSTRAINT-COVERAGE-v1';
const digest=o=>crypto.createHash('sha256').update(JSON.stringify(o)).digest('hex');
function fixtures(){
 const result=[],add=(id,group,rule,make,error)=>result.push({id,group,rule,make,error});
 const fields=[['name','Bug report'],['about','Report a reproducible defect'],['title','""'],['labels','bug'],['assignees','""']];
 const headings=['Description','Steps to reproduce','Expected behavior','Actual behavior','Environment','Supporting evidence'];
 const replace=(a,b)=>{if(!TEMPLATE.includes(a))throw Error('BAD_FIXTURE_SOURCE');return TEMPLATE.replace(a,b)};
 for(const [k,v]of fields){
  add('field-value-'+k,'fields','FIELD_VALUE',()=>replace(k+': '+v,k+': '+v+' other'),'FIELD_VALUE');
  add('field-duplicate-'+k,'fields','UNIQUE_FIELD',()=>replace(k+': '+v,k+': '+v+'\n'+k+': '+v),'FRONT_MATTER');
  add('field-removed-'+k,'fields','REQUIRED_FIELD',()=>replace(k+': '+v+'\n',''),'FIELD_DUPLICATE_OR_UNKNOWN');
 }
 for(const h of headings){
  const slug=h.toLowerCase().replaceAll(' ','-');
  add('heading-changed-'+slug,'headings','HEADING_ORDER',()=>replace('## '+h,'## Changed '+h),'HEADINGS');
  add('heading-removed-'+slug,'headings','HEADING_REQUIRED',()=>replace('## '+h+'\n',''),'HEADINGS');
 }
 const rules=[
 ['unknown-field','grammar','FIELD_ALLOWLIST',()=>replace('labels: bug','unknown: bug'),'FIELD_DUPLICATE_OR_UNKNOWN'],
 ['bad-delimiter','grammar','FRONT_MATTER',()=>replace('---\nname:','--\nname:'),'FRONT_MATTER'],
 ['yaml-alias','grammar','NO_YAML_ALIAS',()=>replace('labels: bug','labels: &bug'),'YAML_SPECIAL_OR_DYNAMIC'],
 ['yaml-expression','grammar','NO_INTERPOLATION',()=>replace('labels: bug','labels: $'+'{{ secret }}'),'YAML_SPECIAL_OR_DYNAMIC'],
 ['html-script','body','NO_HTML_SCRIPT',()=>replace('Describe the problem.','<script>alert(1)</script>'),'ACTIVE_OR_LINKED_CONTENT'],
 ['html-comment','body','NO_HTML_COMMENT',()=>replace('Describe the problem.','<!-- note -->'),'ACTIVE_OR_LINKED_CONTENT'],
 ['javascript-url','body','NO_ACTIVE_URL',()=>replace('Describe the problem.','javascript:alert(1)'),'ACTIVE_OR_LINKED_CONTENT'],
 ['data-url','body','NO_DATA_URL',()=>replace('Describe the problem.','data:text/html,abc'),'ACTIVE_OR_LINKED_CONTENT'],
 ['reference-link','body','NO_REFERENCE_LINK',()=>replace('Describe the problem.','[ref]: https://example.invalid'),'ACTIVE_OR_LINKED_CONTENT'],
 ['image-markdown','body','NO_IMAGE_MARKDOWN',()=>replace('Describe the problem.','![img](https://example.invalid)'),'ACTIVE_OR_LINKED_CONTENT'],
 ['redaction-removed','body','REDACTION_REQUIRED',()=>replace('Remove secrets, credentials, and personal information before attaching logs.','Removed.'),'REDACTION_WARNING'],
 ['redaction-duplicate','body','REDACTION_ONCE',()=>replace('Remove secrets, credentials, and personal information before attaching logs.','Remove secrets, credentials, and personal information before attaching logs.\nRemove secrets, credentials, and personal information before attaching logs.'),'REDACTION_WARNING'],
 ['repro-1','body','REPRO_1',()=>replace('\n1.\n','\nI.\n'),'REPRODUCTION_STEPS'],
 ['repro-2','body','REPRO_2',()=>replace('\n2.\n','\nII.\n'),'REPRODUCTION_STEPS'],
 ['repro-3','body','REPRO_3',()=>replace('\n3.\n','\nIII.\n'),'REPRODUCTION_STEPS'],
 ['crlf','encoding','LF_ONLY',()=>TEMPLATE.replace(/\n/g,'\r\n'),'ENCODING'],
 ['final-newline','encoding','TRAILING_LF',()=>TEMPLATE.slice(0,-1),'ENCODING'],
 ['nul','encoding','NO_NUL',()=>TEMPLATE+String.fromCharCode(0),'ENCODING'],
 ['bom','encoding','NO_BOM',()=>String.fromCharCode(65279)+TEMPLATE,'ENCODING'],
 ['size','encoding','SIZE_LIMIT',()=>TEMPLATE+'a'.repeat(8500),'ENCODING'],
 ['root-heading','body','HEADING_LEVEL',()=>replace('## Description','# Description'),'HEADINGS']
 ];
 for(const [id,group,rule,make,error]of rules)add(id,group,rule,make,error);
 return result;
}
function expectedIds(){return fixtures().map(x=>x.id).sort()}
function run({cases=fixtures(),parser=parseTemplate}={}){
 const reference=fixtures(),requiredIds=reference.map(c=>c.id).sort();
 const referenceById=new Map(reference.map(c=>[c.id,c]));
 if(!Array.isArray(cases)||!Array.isArray(requiredIds))throw Error('INVALID_FIXTURES');
 const errors=[],observations=[],seen=new Set(),required=new Set(requiredIds);
 if(requiredIds.length!==required.size)errors.push('DUPLICATE_REQUIRED_ID');
 let baseline;
 try{baseline=parser(TEMPLATE)}catch(e){errors.push('BASELINE_REJECTED:'+e.message)}
 if(!baseline||baseline.fields?.labels!=='bug'||baseline.headings?.length!==6)errors.push('BASELINE_INVALID');
 for(const c of cases){
  if(!c||typeof c.id!=='string'||seen.has(c.id)){errors.push('INVALID_OR_DUPLICATE_FIXTURE');continue}
  seen.add(c.id);
  if(!required.has(c.id))errors.push('UNEXPECTED_FIXTURE:'+c.id);
  const baselineCase=referenceById.get(c.id);
  if(baselineCase&&(baselineCase.error!==c.error||baselineCase.group!==c.group||baselineCase.rule!==c.rule))
   errors.push('FIXTURE_CONTRACT_CHANGED:'+c.id);
  let reason;
  try{
   const mutated=c.make();
   if(typeof mutated!=='string'||mutated===TEMPLATE)reason='NOT_MUTATED';
   else{try{parser(mutated);reason='UNEXPECTED_ACCEPTANCE'}catch(e){reason=e.message}}
  }catch(e){reason='FIXTURE_ERROR:'+e.message}
  const passed=reason===baselineCase?.error;
  if(!passed)errors.push('FIXTURE_FAILED:'+c.id+':'+reason);
  observations.push({id:c.id,group:c.group,rule:c.rule,
   canonicalAccepted:!!baseline,mutationRejectedAsExpected:passed,expectedError:baselineCase?.error??null,observedError:reason});
 }
 for(const id of required)if(!seen.has(id))errors.push('MISSING_FIXTURE:'+id);
 const groups={};
 for(const v of observations)groups[v.group]=(groups[v.group]||0)+1;
 const out={schema:SCHEMA,status:errors.length?'HOLD':'CONSTRAINT_COVERAGE_PASS_NO_EXECUTION',
  required:requiredIds.length,observed:observations.length,groups,baselineAccepted:!!baseline,
  observations,errors,authority:{mayCreatePR:false,mayRetry:false,mayMerge:false,mayWriteDefaultBranch:false},
  governance:{witnesses:['a1','b1','c1'],observerDepth:1,noQuorum:true,isaDefined:false,
   repoCodeExecuted:false,repoCIExecuted:false}};
 return{...out,evidenceSha256:digest(out)};
}
function audit(r){
 if(r?.schema!==SCHEMA||r.status!=='CONSTRAINT_COVERAGE_PASS_NO_EXECUTION'||
 r.errors?.length!==0||r.required!==r.observed||r.baselineAccepted!==true||
 r.observations?.some(x=>x.canonicalAccepted!==true||x.mutationRejectedAsExpected!==true)||
 r.authority?.mayCreatePR!==false||r.authority?.mayMerge!==false||
 r.governance?.repoCodeExecuted!==false)return{status:'HOLD',reason:'BOUNDARY'};
 const {evidenceSha256,...payload}=r;
 return evidenceSha256===digest(payload)?{status:'PASS'}:{status:'HOLD',reason:'DIGEST'};
}
module.exports={SCHEMA,fixtures,expectedIds,run,audit};
