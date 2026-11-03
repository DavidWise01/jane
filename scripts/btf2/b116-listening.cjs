#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),Core=require('./b116-listening-core.cjs');
const root=path.resolve(__dirname,'../..'),outputDir=path.join(root,'b116');fs.mkdirSync(outputDir,{recursive:true});
const lessonsPath=path.join(root,'b115/teaching.json');
const lessonSet=fs.existsSync(lessonsPath)?JSON.parse(fs.readFileSync(lessonsPath,'utf8')):null;
if(!Array.isArray(lessonSet?.cards))throw Error('B115 catalogue absent; run B115 first');
const logPath=path.join(outputDir,'responses.jsonl'),existing=fs.existsSync(logPath)?fs.readFileSync(logPath,'utf8').split(/\r?\n/).filter(Boolean).map(x=>JSON.parse(x)):[];
let candidates=[];
if(process.env.GITHUB_EVENT_PATH){
 const github=JSON.parse(fs.readFileSync(process.env.GITHUB_EVENT_PATH,'utf8'));
 if(github.issue){const e=Core.eventFromIssue(github.issue,lessonSet);if(e)candidates.push(e)}
}
const additions=Core.appendNew(existing,candidates);
if(additions.length)fs.appendFileSync(logPath,additions.map(x=>JSON.stringify(x)).join('\n')+'\n');
const all=existing.concat(additions);
const report={schema:'JANE_B116_LISTENING_V1',generated_at:new Date().toISOString(),family:'DavidWise01/jane',input:'Public GitHub issue observations only',
 available_lessons:lessonSet.cards.length,...Core.summarize(all),
 caveat:'Feedback is attributable to the public GitHub author; it is NOT verified to originate from an autonomous child.'};
fs.writeFileSync(path.join(outputDir,'listening.json'),JSON.stringify(report,null,2)+'\n');
console.log('B116 listening: observed events',all.length,'new',additions.length,'lessons',report.available_lessons);
