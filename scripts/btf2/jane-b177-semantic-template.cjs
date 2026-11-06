'use strict';
const crypto=require('node:crypto');
const {TEMPLATE,TARGET}=require('./jane-b161-formic-agent.cjs');
const {audit:proofAudit}=require('./jane-b168-proof-proposal.cjs');
const {audit:diffAudit}=require('./jane-b176-differential-tree.cjs');
const SCHEMA='JANE-B177-SEMANTIC-ISSUE-TEMPLATE-v1';
const FIELD_NAMES=['name','about','title','labels','assignees'];
const HEADINGS=['Description','Steps to reproduce','Expected behavior','Actual behavior','Environment','Supporting evidence'];
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const digest=o=>sha(JSON.stringify(o));
function hold(reason,proof){
 return{schema:SCHEMA,status:'HOLD',reasons:[reason],repository:proof?.envelope?.repository||null,
  proposalSha256:proof?.sha256||null,mayCreatePR:false,mayRetry:false,mayMerge:false,
  mayWriteDefaultBranch:false,noRepositoryCodeExecuted:true};
}
function parseTemplate(text){
 if(typeof text!=='string'||Buffer.byteLength(text)>8192||text.includes('\0')||
   text.includes('\r')||!text.endsWith('\n')||text.charCodeAt(0)===0xfeff)
  throw Error('ENCODING');
 const lines=text.split('\n');
 if(lines[0]!=='---'||lines[6]!=='---'||lines[7]!=='')throw Error('FRONT_MATTER');
 const fields={};
 for(let i=1;i<6;i++){
  const m=/^([a-z]+): (.*)$/.exec(lines[i]);
  if(!m||!FIELD_NAMES.includes(m[1])||Object.hasOwn(fields,m[1]))throw Error('FIELD_DUPLICATE_OR_UNKNOWN');
  if(/[&*!|>{}\[\]\\]/.test(m[2])||m[2].includes(String.fromCharCode(96))||
     m[2].includes('http')||m[2].includes('$'))throw Error('YAML_SPECIAL_OR_DYNAMIC');
  fields[m[1]]=m[2];
 }
 if(FIELD_NAMES.some(f=>!Object.hasOwn(fields,f)))throw Error('MISSING_FIELD');
 const expected={name:'Bug report',about:'Report a reproducible defect',title:'""',labels:'bug',assignees:'""'};
 if(FIELD_NAMES.some(k=>fields[k]!==expected[k]))throw Error('FIELD_VALUE');
 const body=lines.slice(8);
 if(body.some(x=>/<\/?[A-Za-z!]|javascript:|data:|<%|{%|^\s*!\[|^\s*\[[^\]]+\]:/i.test(x)))
  throw Error('ACTIVE_OR_LINKED_CONTENT');
 const headings=body.filter(x=>x.startsWith('## ')).map(x=>x.slice(3));
 if(JSON.stringify(headings)!==JSON.stringify(HEADINGS))throw Error('HEADINGS');
 if(body.some(x=>x.startsWith('#')&&!x.startsWith('## ')))throw Error('EXTRA_HEADING');
 if(body.filter(x=>x==='Remove secrets, credentials, and personal information before attaching logs.').length!==1)
  throw Error('REDACTION_WARNING');
 for(const step of ['1.','2.','3.'])if(body.filter(x=>x===step).length!==1)throw Error('REPRODUCTION_STEPS');
 return{fields,headings,bytes:Buffer.byteLength(text),sha256:sha(Buffer.from(text))};
}
function inspect(proof,diff){
 if(proofAudit(proof).status!=='PASS')return hold('B168_UNVERIFIED',proof);
 if(diffAudit(diff).status!=='PASS')return hold('B176_UNVERIFIED',proof);
 const e=proof.envelope,change=e.proposal?.changes?.[0];
 if(e.proposal?.changes?.length!==1||change?.operation!=='ADD_FILE'||change.path!==TARGET||
  diff.repository!==e.repository||diff.proposalSha256!==proof.sha256||diff.baseSha!==e.base?.commitSha||
  diff.independentAddedPaths?.length!==1||diff.independentAddedPaths[0]!==TARGET)
  return hold('EVIDENCE_SCOPE',proof);
 let parsed;
 try{parsed=parseTemplate(change.after)}catch(err){return hold('SEMANTIC_'+err.message,proof)}
 if(change.after!==TEMPLATE||parsed.sha256!==change.afterSha256)return hold('CANONICAL_MISMATCH',proof);
 const out={schema:SCHEMA,status:'SEMANTICALLY_VALID_FIXED_TEMPLATE_NO_EXECUTION',reasons:[],
  repository:e.repository,proposalSha256:proof.sha256,baseSha:e.base.commitSha,treeSha:diff.sourceTreeSha,
  b176Attestation:diff.attestationSha256,template:parsed,checks:['FIELD_ALLOWLIST','UNIQUE_FIELDS',
  'SAFE_VALUES','HEADING_ORDER','NO_ACTIVE_MARKUP','REDACTION','REPRO_STEPS','CANONICAL_SHA256'],
  noRepositoryCodeExecuted:true,targetRepositoryCiExecuted:false,
  mayCreatePR:false,mayRetry:false,mayMerge:false,mayWriteDefaultBranch:false};
 return{...out,attestationSha256:digest(out)};
}
function audit(report){
 if(report?.schema!==SCHEMA||report.status!=='SEMANTICALLY_VALID_FIXED_TEMPLATE_NO_EXECUTION'||
  report.noRepositoryCodeExecuted!==true||report.targetRepositoryCiExecuted!==false||
  report.mayCreatePR!==false||report.mayRetry!==false||report.mayMerge!==false||
  report.mayWriteDefaultBranch!==false||report.checks?.length!==8)return{status:'HOLD',reason:'BOUNDARY'};
 const {attestationSha256,...original}=report;
 return attestationSha256===digest(original)?{status:'PASS',attestationSha256}:{status:'HOLD',reason:'DIGEST'};
}
function registry(results){
 if(!Array.isArray(results)||results.length>8)throw Error('B177_RECORD_LIMIT');
 return{schema:'JANE-B177-SEMANTIC-REGISTRY-v1',mode:'READ_ONLY',
  status:results.length?'OBSERVATIONS_RECORDED':'HOLD_NO_PROPOSALS',results,
  counts:{observed:results.length,valid:results.filter(x=>x.status==='SEMANTICALLY_VALID_FIXED_TEMPLATE_NO_EXECUTION').length,
    held:results.filter(x=>x.status==='HOLD').length},
  governance:{witnesses:['a1','b1','c1'],observerDepth:1,noQuorum:true,isaDefined:false,
    automaticWrites:false,automaticMerges:false,targetRepositoryCodeExecuted:false}};
}
module.exports={parseTemplate,inspect,audit,registry,hold};
