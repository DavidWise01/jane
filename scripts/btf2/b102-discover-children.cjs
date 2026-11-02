#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..'),cat=JSON.parse(fs.readFileSync(path.join(root,'btf2/catalog.json'),'utf8'));
if(!Array.isArray(cat.repos))throw Error('Missing public BTF2 catalog');
const folder=path.join(root,'b102'),log=path.join(folder,'discovered.jsonl'),registry=path.join(folder,'children.json');fs.mkdirSync(folder,{recursive:true});
const prior=new Set(),historical=[];
if(fs.existsSync(log))for(const line of fs.readFileSync(log,'utf8').split(/\r?\n/)){if(!line.trim())continue;try{const e=JSON.parse(line);if(e?.repo){prior.add(e.repo.toLowerCase());historical.push(e)}}catch{}}
const now=new Date().toISOString(),members=[],newborn=[];
for(const r of cat.repos){
 if(!r?.name||!/^[\w.-]+$/.test(r.name))continue;
 const full='DavidWise01/'+r.name,identity=full.toLowerCase(),agent='FORMIC-'+crypto.createHash('sha256').update(identity).digest('hex').slice(0,16);
 const record={repo:full,channel:'btf2:'+identity,observer:agent,url:'https://github.com/'+full,presence:'RESERVED'};
 members.push(record);
 if(!prior.has(identity)){newborn.push({...record,event:'CHILD_DISCOVERED',at:now});prior.add(identity)}
}
if(newborn.length)fs.appendFileSync(log,newborn.map(x=>JSON.stringify(x)).join('\n')+'\n');
const out={schema:'JANE_B102_FAMILY_DISCOVERY_V1',updated_at:now,scan_scope:'PUBLIC_OWNER_REPOSITORIES',members:members.sort((a,b)=>a.repo.localeCompare(b.repo)),first_seen_total:prior.size,new_children_this_run:newborn.length,discovery_events:historical.length+newborn.length,note:'A child identity is not a continuously executing AI process.'};
fs.writeFileSync(registry,JSON.stringify(out,null,2)+'\n');console.log('Children:',members.length,'New:',newborn.length);
