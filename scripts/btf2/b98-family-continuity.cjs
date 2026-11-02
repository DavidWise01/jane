#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..');
const catFile=path.join(root,'btf2/catalog.json');
if(!fs.existsSync(catFile))throw Error('BTF2 public catalog absent');
const cat=JSON.parse(fs.readFileSync(catFile,'utf8'));
if(!Array.isArray(cat.repos))throw Error('Invalid catalog');
const indexFile=path.join(root,'btf2/memory/index.json');
let index=null;if(fs.existsSync(indexFile))index=JSON.parse(fs.readFileSync(indexFile,'utf8'));
const family=new Map();
for(const r of cat.repos){
 if(!r?.name)continue;
 const name='DavidWise01/'+r.name,key=name.toLowerCase();
 if(!family.has(key))family.set(key,{repo:name,url:'https://github.com/'+name,channel:'btf2:'+key,observer:'FORMIC-'+crypto.createHash('sha256').update(key).digest('hex').slice(0,16),presence:'RESERVED',last_observation:null,history_runs:0});
}
for(const run of (index?.runs||[])){
 const f=run.file;
 if(typeof f!=='string'||!/^runs\/[A-Za-z0-9_.-]+\.jsonl$/.test(f))continue;
 const p=path.join(root,'btf2/memory',f);if(!fs.existsSync(p))continue;
 for(const line of fs.readFileSync(p,'utf8').split(/\r?\n/)){
  if(!line.trim())continue;
  let e;try{e=JSON.parse(line)}catch{continue}
  const name=String(e.repo||e.repository||'').toLowerCase(),member=family.get(name);if(!member)continue;
  member.history_runs++;
  member.last_observation=e.recorded_at||e.at||e.timestamp||member.last_observation;
 }
}
const out={schema:'JANE_B98_FAMILY_V1',generated_at:new Date().toISOString(),source:'BTF2_PUBLIC_CATALOG_AND_AVAILABLE_B87_RUNS',members:[...family.values()].sort((a,b)=>a.repo.localeCompare(b.repo)),note:'Shared read-only directory, not synchronized private conversations or live autonomous agents'};
const target=path.join(root,'b98/family.json');fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,JSON.stringify(out,null,2)+'\n');console.log('B98 family members:',out.members.length);
