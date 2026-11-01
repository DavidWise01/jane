#!/usr/bin/env node
// B82 deterministic bounded governance-corpus audit. Read-only. No autonomous remote actions.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..'),dir=path.join(root,'governance');
const required=[
['B70','JANE-B70-SOVEREIGN-DELEGATION-v1.0.md'],
['B71','JANE-B71-FORMIC-HIVE-v1.0.md'],
['B72','JANE-B72-STIGMERGIC-MEMORY-v1.0.md'],
['B73','JANE-B73-ADAPTIVE-SWARM-TOPOLOGY-v1.0.md'],
['B74','JANE-B74-COLONY-RESILIENCE-v1.0.md'],
['B75','JANE-B75-COLONY-REGENERATION-v1.0.md'],
['B76','JANE-B76-CARRYING-CAPACITY-v1.0.md'],
['B77','JANE-B77-RESOURCE-SHOCK-v1.0.md'],
['B78','JANE-B78-HYSTERETIC-RECOVERY-v1.0.md'],
['B79','JANE-B79-FEEDBACK-CALIBRATION-v1.0.md'],
['B80','JANE-B80-UNCERTAINTY-ADAPTATION-v1.0.md'],
['B81','JANE-B81-REPEATED-ANOMALY-v1.0.md'],
['B82','JANE-B82-PROVENANCE-CAUSE-HYPOTHESES-v1.0.md']
];
const observed=[];for(const [id,name] of required){const file=path.join(dir,name);const exists=fs.existsSync(file);const content=exists?fs.readFileSync(file,'utf8'):'';const sha256=exists?crypto.createHash('sha256').update(content).digest('hex'):null;
const checks={exists,mentions_jane:/\bJane\b/i.test(content),mentions_root:/\b(Peter|HEGEMON|0root)\b/i.test(content),mentions_nonblocking:/\b(no quorum|no completion|completion.*not|non.?block|without waiting|no worker veto|no subordinate veto|without.*completion)\b/i.test(content),mentions_register:/a\(self\)/i.test(content)};
observed.push({bound:id,file:'governance/'+name,sha256,checks,notes:!exists?['MISSING_FILE']:Object.entries(checks).filter(([k,v])=>k!=='exists'&&!v).map(([k])=>'REVIEW_'+k.toUpperCase())});}
const paired=required.map(([id])=>({id,page:'b'+id.slice(1).padStart(2,'0')+'/index.html'})).filter(x=>Number(x.id.slice(1))>=71);
const pageChecks=paired.map(x=>({...x,exists:fs.existsSync(path.join(root,x.page))}));
const findings=[...observed.flatMap(x=>x.notes.map(note=>({bound:x.bound,type:note}))),...pageChecks.filter(x=>!x.exists).map(x=>({bound:x.id,type:'MISSING_PAGE',path:x.page}))];
const report={schema:'jane-b82-audit-1',mode:'READ_ONLY',scope:'B70-B82 governance and B71-B82 pages',governance:'PETER HEGEMON:T128 / JANE T000-T127',interpretation:'String checks are review cues, not semantic proof, policy decisions, or agent authority.',observed, pageChecks, findings,totals:{governance_files_present:observed.filter(x=>x.checks.exists).length,governance_files_expected:required.length,pages_present:pageChecks.filter(x=>x.exists).length,pages_expected:pageChecks.length,review_cues:findings.length}};
const out=path.join(root,'b82','audit-report.json');fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report.totals));console.log('Report:',out);
