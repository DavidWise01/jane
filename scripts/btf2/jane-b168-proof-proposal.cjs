'use strict';
/**
 * B168 proof-carrying proposal. A signed-off evidence envelope is not a write grant.
 * Pure deterministic planning: no GitHub mutations, no automatic retries or merges.
 */
const crypto=require('node:crypto');
const {TEMPLATE,TARGET,BRANCH,repoGate,policyGate}=require('./jane-b161-formic-agent.cjs');
const OWNER='DavidWise01',REPAIR='BUG_REPORT_TEMPLATE',FORMAT='JANE-B168-PROOF-CARRYING-PROPOSAL-v1';
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const pristine=o=>JSON.parse(JSON.stringify(o));
function build({repo,policy,baseSha,targetExists=false,b167,checks=['FORMIC_POLICY_GATE','FORMIC_DIFF_INTEGRITY','REPO_CI'],observedAt='2026-11-05T00:00:00Z'}){
 if(repoGate(repo)!=='ELIGIBLE')return{status:'HOLD',reason:'REPOSITORY_SCOPE'};
 if(policyGate(policy)!=='ELIGIBLE')return{status:'HOLD',reason:'REPOSITORY_POLICY'};
 if(targetExists)return{status:'NO_CHANGE',reason:'TARGET_ALREADY_PRESENT'};
 if(!/^[a-f0-9]{40}$/i.test(baseSha||''))return{status:'HOLD',reason:'BASE_SHA_REQUIRED'};
 if(!Number.isFinite(Date.parse(observedAt)))return{status:'HOLD',reason:'INVALID_TIMESTAMP'};
 if(b167?.repository!==repo.full_name||b167?.status!=='POLICY_EVIDENCE_PRESENT'||
    b167?.mayCreatePR!==false||b167?.mayRetry!==false||b167?.mayMerge!==false)
    return{status:'HOLD',reason:'B167_POLICY_EVIDENCE_REQUIRED'};
 if(!Array.isArray(checks)||!checks.length||checks.length>20||new Set(checks).size!==checks.length||
    !checks.every(c=>typeof c==='string'&&/^[A-Z0-9_-]{3,80}$/.test(c)))return{status:'HOLD',reason:'INVALID_EXPECTED_CHECKS'};
 const before=null,after=TEMPLATE;
 const contentHash=hash(Buffer.from(after,'utf8'));
 const entry={operation:'ADD_FILE',path:TARGET,before,after,afterSha256:contentHash,
    unifiedDiff:['--- /dev/null','+++ b/'+TARGET,'@@ -0,0 +1,'+after.replace(/\n$/,'').split('\n').length+' @@',
      ...after.replace(/\n$/,'').split('\n').map(line=>'+'+line)].join('\n')+'\n'};
 const envelope={
  schema:FORMAT,repository:repo.full_name,repair:REPAIR,
  base:{branch:repo.default_branch,commitSha:baseSha},
  proposal:{branch:BRANCH,changes:[entry],changeCount:1},
  policyEvidence:{type:'B167_READ_ONLY',result:b167.status,repository:b167.repository},
  checks:{expected:[...checks],observed:[],verified:false},
  safety:{writeAuthorized:false,draftPrAuthorized:false,mergeAuthorized:false,autoRetry:false,
    defaultBranchWrites:false,execution:'NOT_EXECUTED'},
  observedAt,source:'B161_FIXED_TEMPLATE_AND_B167_EVIDENCE'
 };
 return{status:'PROPOSAL_ONLY',envelope,sha256:hash(Buffer.from(JSON.stringify(envelope),'utf8'))};
}
function audit(record){
 if(record?.status!=='PROPOSAL_ONLY'||record?.envelope?.schema!==FORMAT)return{status:'HOLD',reason:'SCHEMA'};
 const e=record.envelope;
 if(!/^DavidWise01\/[A-Za-z0-9._-]+$/.test(e.repository||'')||e.repair!==REPAIR||
   !/^[a-f0-9]{40}$/i.test(e.base?.commitSha||'')||
   e.proposal?.branch!==BRANCH||e.proposal?.changeCount!==1||
   e.proposal?.changes?.length!==1||e.checks?.verified!==false||
   !Array.isArray(e.checks?.expected)||!e.checks.expected.length||
   e.safety?.writeAuthorized!==false||e.safety?.draftPrAuthorized!==false||
   e.safety?.mergeAuthorized!==false||e.safety?.autoRetry!==false||
   e.safety?.defaultBranchWrites!==false||e.safety?.execution!=='NOT_EXECUTED'||
   e.policyEvidence?.result!=='POLICY_EVIDENCE_PRESENT'||e.policyEvidence?.repository!==e.repository)
   return{status:'HOLD',reason:'BOUNDARY'};
 const change=e.proposal.changes[0];
 if(change.operation!=='ADD_FILE'||change.path!==TARGET||change.before!==null||change.after!==TEMPLATE||
   change.afterSha256!==hash(Buffer.from(change.after,'utf8')))
   return{status:'HOLD',reason:'DIFF_CONTENT'};
 const expected=['--- /dev/null','+++ b/'+TARGET,'@@ -0,0 +1,'+TEMPLATE.replace(/\n$/,'').split('\n').length+' @@',
   ...TEMPLATE.replace(/\n$/,'').split('\n').map(x=>'+'+x)].join('\n')+'\n';
 if(change.unifiedDiff!==expected)return{status:'HOLD',reason:'DIFF_TEXT'};
 if(record.sha256!==hash(Buffer.from(JSON.stringify(e),'utf8')))return{status:'HOLD',reason:'ENVELOPE_DIGEST'};
 return{status:'PASS',sha256:record.sha256,changes:1,writeAuthorized:false};
}
function registry(records){
 if(!Array.isArray(records))throw Error('INVALID_PROPOSAL_LIST');
 const sorted=[...records].sort((a,b)=>String(a.envelope?.repository||'').localeCompare(String(b.envelope?.repository||'')));
 const duplicate=new Set();
 return{schema:'JANE-B168-PROPOSAL-REGISTRY-v1',mode:'READ_ONLY',
  entries:sorted.map(rec=>{
   if(audit(rec).status!=='PASS')throw Error('UNVERIFIED_PROPOSAL');
   if(duplicate.has(rec.envelope.repository))throw Error('DUPLICATE_REPOSITORY');
   duplicate.add(rec.envelope.repository);
   return pristine(rec);
  }),
  governance:{observerDepth:1,witnesses:['a1','b1','c1'],noQuorum:true,isaDefined:false,autoWrites:false,autoMerge:false}};
}
module.exports={OWNER,REPAIR,FORMAT,build,audit,registry};
