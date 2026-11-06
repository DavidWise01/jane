'use strict';
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const {TEMPLATE}=require('./jane-b161-formic-agent.cjs');
const {build}=require('./jane-b168-proof-proposal.cjs');
const {parseTemplate,inspect,audit,registry}=require('./jane-b177-semantic-template.cjs');
const repo={full_name:'DavidWise01/jane',default_branch:'main',private:false,visibility:'public',archived:false,disabled:false,fork:false};
const policy={schema:'FORMIC-REPO-POLICY-v1',enabled:true,allowed_repairs:['BUG_REPORT_TEMPLATE'],max_open_pull_requests:1};
const b167={repository:repo.full_name,status:'POLICY_EVIDENCE_PRESENT',mayCreatePR:false,mayRetry:false,mayMerge:false};
const proof=build({repo,policy,b167,baseSha:'a'.repeat(40)});
assert.equal(parseTemplate(TEMPLATE).fields.labels,'bug');
for(const changed of [
 TEMPLATE.replace('labels: bug','labels: admin'),
 TEMPLATE.replace('name: Bug report','name: &alias'),
 TEMPLATE.replace('about: Report a reproducible defect','about: javascript:alert(1)'),
 TEMPLATE.replace('## Environment','## Unapproved'),
 TEMPLATE.replace('Remove secrets, credentials, and personal information before attaching logs.','<script>alert(1)</script>'),
 TEMPLATE.replace('labels: bug','labels: bug\nlabels: bug'),
 TEMPLATE.replace(/\n/g,'\r\n')
])assert.throws(()=>parseTemplate(changed));
const diff={schema:'JANE-B176-DIFFERENTIAL-TREE-AUDIT-v1',status:'DIFFERENTIAL_TREE_AGREEMENT_NO_EXECUTION',
 reasons:[],repository:repo.full_name,proposalSha256:proof.sha256,baseSha:'a'.repeat(40),
 sourceTreeSha:'b'.repeat(40),b174ManifestSha256:'c'.repeat(64),
 independentBeforeSha256:'d'.repeat(64),independentAfterSha256:'e'.repeat(64),
 independentAddedPaths:['.github/ISSUE_TEMPLATE/bug_report.md'],independentPreservedCount:1,
 identicalBefore:true,identicalAfter:true,independentAlgorithm:true,
 targetRepositoryCodeExecuted:false,targetRepositoryCiExecuted:false,
 mayCreatePR:false,mayRetry:false,mayMerge:false,mayWriteDefaultBranch:false};
diff.attestationSha256=crypto.createHash('sha256').update(JSON.stringify(diff)).digest('hex');
const good=inspect(proof,diff);assert.equal(good.status,'SEMANTICALLY_VALID_FIXED_TEMPLATE_NO_EXECUTION');
assert.equal(audit(good).status,'PASS');assert.equal(good.mayCreatePR,false);
const wrong=inspect(proof,{...diff,independentAddedPaths:['wrong.md']});assert.equal(wrong.status,'HOLD');
const unsafe={...good,mayMerge:true};assert.equal(audit(unsafe).status,'HOLD');
assert.equal(registry([good,wrong]).counts.held,1);
console.log('PASS B177: semantic field grammar, ordered headings, no active markup, B176 scope, no writes');
