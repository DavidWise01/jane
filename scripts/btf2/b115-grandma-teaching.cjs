#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),Core=require('./b115-teaching-core.cjs');
const root=path.resolve(__dirname,'../..'),get=p=>{const f=path.join(root,p);return fs.existsSync(f)?JSON.parse(fs.readFileSync(f,'utf8')):null};
const lessons=get('b114/lessons.json');if(!lessons)throw Error('B114 lessons missing: run B114 first');
if(lessons.source_verified!=='SHA256_B87_RUNS')throw Error('Refuse unverified B114 source');
const registry=get('b113/family.json'),prior=get('b115/teaching.json')||{};
const r=Core.build(lessons,registry,prior),folder=path.join(root,'b115');fs.mkdirSync(folder,{recursive:true});
const eventsFile=path.join(folder,'catalogue.jsonl');
if(r.newEvents.length)fs.appendFileSync(eventsFile,r.newEvents.map(e=>JSON.stringify({...e,at:new Date().toISOString()})).join('\n')+'\n');
const out={schema:'JANE_B115_TEACHING_MEMORY_V1',generated_at:new Date().toISOString(),source:'b114/lessons.json',evidence_scope:lessons.scope||'PUBLIC_GITHUB_METADATA_ONLY',
family_registry_available:!!registry,lesson_count:r.cards.length,suggestion_count:r.suggestions.length,
cards:r.cards,suggestions:r.suggestions,
policy:'Optional suggestions only, no message delivery, no verified causal inference, no autonomous agents or compulsory teaching.'};
fs.writeFileSync(path.join(folder,'teaching.json'),JSON.stringify(out,null,2)+'\n');
console.log('B115',r.cards.length,'evidence cards',r.suggestions.length,'optional relevant suggestions',r.newEvents.length,'new catalogue events');
