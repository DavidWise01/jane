#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..');
const catalogPath=path.join(root,'btf2','catalog.json');
if(!fs.existsSync(catalogPath))throw Error('BTF2 catalog missing; run public repo discovery');
const catalog=JSON.parse(fs.readFileSync(catalogPath,'utf8'));
if(!Array.isArray(catalog.repos))throw Error('Invalid catalog');
const colPath=path.join(root,'b88','collation.json');
const collation=fs.existsSync(colPath)?JSON.parse(fs.readFileSync(colPath,'utf8')):null;
const states=new Map((collation?.events||[]).map(x=>[String(x.repo||'').toLowerCase(),x.status]));
const unique=new Map();
for(const r of catalog.repos){if(!r?.name||!/^https:\/\/github\.com\/DavidWise01\//i.test(r.url||''))continue;unique.set(r.name.toLowerCase(),r)}
const pins=[...unique.values()].sort((a,b)=>a.name.localeCompare(b.name)).map(r=>{
 const key='DavidWise01/'+r.name,hash=crypto.createHash('sha256').update(key.toLowerCase()).digest('hex');
 const slot=(parseInt(hash.slice(0,8),16)%184)+1;
 return {pin:'BTF2',repo:key,url:r.url,agent_id:'FORMIC-'+hash.slice(0,16),hon184_slot:slot,band:slot<=61?'H':slot<=122?'O':'N',observation_status:states.get(key.toLowerCase())||'UNKNOWN',archived:!!r.archived,fork:!!r.fork};
});
const slots=Array.from({length:184},(_,i)=>({slot:i+1,occupancy:0}));
for(const p of pins)slots[p.hon184_slot-1].occupancy++;
const output={schema:'HON184_B89_V1',mission:'HEGEMON M001 / Internet Time Dilation',generated_at:new Date().toISOString(),status:'DERIVED_GITHUB_PUBLIC_METADATA',slot_count:184,pin_count:pins.length,collision_slots:slots.filter(s=>s.occupancy>1).length,unknown_count:pins.filter(p=>p.observation_status==='UNKNOWN').length,source:'BTF2 PUBLIC CATALOG',pins,slots};
const out=path.join(root,'b89','hon184.json');fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(output,null,2)+'\n');console.log(JSON.stringify({pins:output.pin_count,slots:184,collision_slots:output.collision_slots,unknown:output.unknown_count}));
