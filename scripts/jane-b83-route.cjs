#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..'),input=path.join(root,'b82','audit-report.json'),output=path.join(root,'b83','work-packet.json');
if(!fs.existsSync(input)){console.error('B82 report missing; run node scripts/jane-b82-audit.cjs first');process.exit(1)}
const report=JSON.parse(fs.readFileSync(input,'utf8'));
if(!Array.isArray(report.findings))throw Error('Unrecognized report: findings must be array');
if(report.findings.length>200)throw Error('Bounded capacity exceeded: max 200 finding entries');
const roles=['observer','auditor','verifier'];
const assignments=report.findings.map((f,i)=>{
const cue=typeof f.type==='string'?f.type:'UNKNOWN_CUE',bound=typeof f.bound==='string'?f.bound:'UNKNOWN_BOUND';
const role=cue.startsWith('MISSING_')?'observer':cue.startsWith('REVIEW_')?'auditor':'verifier';
return {work_id:'B83-'+String(i+1).padStart(4,'0'),source:{bound,cue,path:typeof f.path==='string'?f.path:null},assigned_slot:role+'-'+String(i%3+1).padStart(2,'0'),role,capability:'READ_ONLY',status:'SUGGESTED_NOT_EXECUTED',reason:'Textual audit cue requires contextual inspection; not a proven violation'};
});
const packet={schema:'jane-b83-routing-v1',origin:'B82_FILE_AUDIT',report_sha256:crypto.createHash('sha256').update(fs.readFileSync(input)).digest('hex'),authority:'PETER:T128 / JANE:T000-T127',mode:'ROUTE_ONLY',worker_processes_started:0,assignments,summary:{candidate_findings:report.findings.length,assigned:assignments.length,roles:roles.map(role=>({role,count:assignments.filter(x=>x.role===role).length}))},warning:'Assignments are simulated/read-only work suggestions; agents are not running'};
fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(packet,null,2)+'\n');
console.log(JSON.stringify(packet.summary));console.log('Wrote',output);
