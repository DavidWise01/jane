#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),G=require('./b113-generation-core.cjs');
const root=path.resolve(__dirname,'../..');const r=p=>{const f=path.join(root,p);return fs.existsSync(f)?JSON.parse(fs.readFileSync(f,'utf8')):null};
const b112=r('b112/registry.json'),b102=r('b102/children.json');if(!b112?.members?.length)throw Error('Run B112 FORMIC lattice first');
const folder=path.join(root,'b113'),existing=r('b113/family.json'),history={};
for(const x of [...(existing?.members||[]),...(existing?.reserved_members||[])])history[x.repo.toLowerCase()]=x;
const firsts=new Map();const discover=path.join(root,'b102/discovered.jsonl');if(fs.existsSync(discover)){for(const line of fs.readFileSync(discover,'utf8').split(/\r?\n/)){try{const ev=JSON.parse(line);if(ev.event==='CHILD_DISCOVERED'&&ev.repo&&ev.at){let k=ev.repo.toLowerCase();if(!firsts.has(k)||ev.at<firsts.get(k))firsts.set(k,ev.at)}}catch{}}}
const previous=new Map((b102?.members||[]).map(x=>[x.repo.toLowerCase(),x]));
const merged=b112.members.map(m=>({...m,first_seen:firsts.get(m.repo.toLowerCase())||null,presence:previous.get(m.repo.toLowerCase())?.presence||m.presence}));
const now=new Date().toISOString(),result=G.normalize(merged,history,now),active=new Set(result.members.map(x=>x.repo.toLowerCase()));
const reserved_members=[...(existing?.reserved_members||[]),...(existing?.members||[])].filter((x,i,a)=>!active.has(x.repo.toLowerCase())&&a.findIndex(y=>y.repo.toLowerCase()===x.repo.toLowerCase())===i);
const cohorts={};for(const x of result.members)cohorts[x.generation]=(cohorts[x.generation]||0)+1;
const payload={schema:'JANE_B113_GRANDMOTHER_CONTINUITY_V1',generated_at:now,source:'B112 stable hex + B102 append-only discovery events',scope:'PUBLIC_REPOS_ONLY',member_count:result.members.length,cohorts,unknown_lineage_count:result.members.filter(x=>x.lineage.parentage==='UNKNOWN').length,members:result.members,reserved_members,note:'Arrival cohorts are observed discovery dates, not genealogical generations. No autonomous child execution is implied.'};
fs.mkdirSync(folder,{recursive:true});fs.writeFileSync(path.join(folder,'family.json'),JSON.stringify(payload,null,2)+'\n');
if(result.events.length)fs.appendFileSync(path.join(folder,'births.jsonl'),result.events.map(x=>JSON.stringify(x)).join('\n')+'\n');
console.log('B113 Grandma family',payload.member_count,'arrival cohorts',Object.keys(cohorts).length,'new registrations',result.events.length);
