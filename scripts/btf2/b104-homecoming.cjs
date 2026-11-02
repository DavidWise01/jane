#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
function read(p){const f=path.join(root,p);return fs.existsSync(f)?JSON.parse(fs.readFileSync(f,'utf8')):null}
const source=read('b103/family.json')||read('b102/children.json');
const children=source?.children||source?.members||[];
if(!Array.isArray(children)||!children.length)throw Error('Run B103 or B102 discovery before B104');
const uniq=new Map();
for(const m of children){const repo=String(m.repo||'');if(!/^DavidWise01\/[A-Za-z0-9_.-]+$/i.test(repo))continue;const key=repo.toLowerCase();if(uniq.has(key))continue;uniq.set(key,{repo,formic:m.formic||m.observer||null,channel:m.channel||'btf2:'+key,first_seen:m.first_seen||null,presence:m.presence||'RESERVED',github_url:m.home||m.url||'https://github.com/'+repo,home_url:'https://0root.ai/',home_relation:'FAMILY_HOME_REFERENCE_ONLY',corpus_matches:[],corpus_status:'UNVERIFIED'})}
const out={schema:'JANE_B104_HOMECOMING_V1',generated_at:new Date().toISOString(),home:{url:'https://0root.ai/',role:'USER_DESIGNATED_FAMILY_HOME',availability:'UNVERIFIED',corpus:'UNVERIFIED'},children:[...uniq.values()].sort((a,b)=>a.repo.localeCompare(b.repo)),description:'Derived family-home map; no website content, writable bridge or autonomous worker inferred.'};
const d=path.join(root,'b104');fs.mkdirSync(d,{recursive:true});fs.writeFileSync(path.join(d,'homecoming.json'),JSON.stringify(out,null,2)+'\n');console.log('Homecoming children',out.children.length);
